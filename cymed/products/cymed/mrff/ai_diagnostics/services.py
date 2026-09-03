"""Service layer for CyMed MRFF ai_diagnostics governance workflows."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import (
    BiasAudit,
    Deployment,
    DriftMetric,
    HitlReviewItem,
    HitlReviewQueue,
    InferenceOutcome,
    ModelCard,
)


DEFAULT_BASELINE_SENSITIVITY = Decimal("0.85")
EQUITY_DELTA_THRESHOLD = Decimal("0.05")
POSITIVE_CONFIDENCE_THRESHOLD = Decimal("0.5")


@transaction.atomic
def publish_model_card(
    *,
    ai_model_id: str,
    version: str,
    intended_use: str,
    tenant_id: str | None = None,
    target_population: str = "",
    clinical_workflow: str = "",
    inputs_description: str = "",
    outputs_description: str = "",
    performance: dict[str, Any] | None = None,
    validation_datasets: list[Any] | None = None,
    known_limitations: str = "",
    ethical_considerations: str = "",
    maintainer_email: str = "",
    regulatory_kind: str = "unknown",
    regulatory_reference: str = "",
    tga_artg_number: str = "",
) -> ModelCard:
    card, _created = ModelCard.objects.update_or_create(
        ai_model_id=ai_model_id,
        version=version,
        defaults={
            "tenant_id": tenant_id,
            "intended_use": intended_use,
            "target_population": target_population,
            "clinical_workflow": clinical_workflow,
            "inputs_description": inputs_description,
            "outputs_description": outputs_description,
            "performance": performance or {},
            "validation_datasets": validation_datasets or [],
            "known_limitations": known_limitations,
            "ethical_considerations": ethical_considerations,
            "maintainer_email": maintainer_email,
            "regulatory_kind": regulatory_kind,
            "regulatory_reference": regulatory_reference,
            "tga_artg_number": tga_artg_number,
            "published_at": timezone.now(),
        },
    )
    return card


@transaction.atomic
def deploy(
    *,
    tenant_id: str,
    ai_model_id: str,
    version: str,
    environment: str = "canary",
    traffic_percent: int = 10,
    deployed_by_profile_id: str | None = None,
) -> Deployment:
    deployment = Deployment.objects.create(
        tenant_id=tenant_id,
        ai_model_id=ai_model_id,
        version=version,
        environment=environment,
        traffic_percent=int(traffic_percent),
        started_at=timezone.now(),
        deployed_by_profile_id=deployed_by_profile_id,
    )
    return deployment


@transaction.atomic
def promote(
    *,
    deployment_id: str,
    environment: str,
    traffic_percent: int,
) -> Deployment:
    deployment = Deployment.objects.get(id=deployment_id)
    deployment.environment = environment
    deployment.traffic_percent = int(traffic_percent)
    deployment.save(
        update_fields=["environment", "traffic_percent", "updated_at"]
    )
    return deployment


@transaction.atomic
def retire(
    *,
    deployment_id: str,
    rollback_reason: str = "",
) -> Deployment:
    deployment = Deployment.objects.get(id=deployment_id)
    deployment.environment = Deployment.Environment.RETIRED
    deployment.traffic_percent = 0
    deployment.ended_at = timezone.now()
    deployment.rollback_reason = rollback_reason
    deployment.save(
        update_fields=[
            "environment",
            "traffic_percent",
            "ended_at",
            "rollback_reason",
            "updated_at",
        ]
    )
    return deployment


def _classify_outcome(
    *,
    predicted_kind: str,
    predicted_confidence: Decimal,
    ground_truth_kind: str,
) -> str:
    if not ground_truth_kind:
        return InferenceOutcome.Outcome.UNKNOWN
    predicted_positive = (
        bool(predicted_kind)
        and predicted_confidence >= POSITIVE_CONFIDENCE_THRESHOLD
    )
    truth_positive = bool(ground_truth_kind) and ground_truth_kind.lower() not in {
        "negative",
        "none",
        "normal",
    }
    if predicted_positive and truth_positive:
        if (
            predicted_kind
            and ground_truth_kind
            and predicted_kind == ground_truth_kind
        ):
            return InferenceOutcome.Outcome.TRUE_POSITIVE
        return InferenceOutcome.Outcome.FALSE_POSITIVE
    if predicted_positive and not truth_positive:
        return InferenceOutcome.Outcome.FALSE_POSITIVE
    if not predicted_positive and truth_positive:
        return InferenceOutcome.Outcome.FALSE_NEGATIVE
    return InferenceOutcome.Outcome.TRUE_NEGATIVE


@transaction.atomic
def record_outcome(
    *,
    deployment_id: str,
    study_instance_uid: str,
    inference_run_id: str | None = None,
    predicted_kind: str = "",
    predicted_confidence: Decimal = Decimal("0"),
    ground_truth_kind: str = "",
    ground_truth_source: str = "unknown",
    reviewer_profile_id: str | None = None,
    note: str = "",
) -> InferenceOutcome:
    confidence = Decimal(str(predicted_confidence))
    outcome_value = _classify_outcome(
        predicted_kind=predicted_kind,
        predicted_confidence=confidence,
        ground_truth_kind=ground_truth_kind,
    )
    outcome = InferenceOutcome.objects.create(
        deployment_id=deployment_id,
        study_instance_uid=study_instance_uid,
        inference_run_id=inference_run_id,
        predicted_kind=predicted_kind,
        predicted_confidence=confidence,
        ground_truth_kind=ground_truth_kind,
        ground_truth_source=ground_truth_source,
        outcome=outcome_value,
        reviewed_at=timezone.now() if reviewer_profile_id else None,
        reviewer_profile_id=reviewer_profile_id,
        note=note,
    )
    return outcome


@transaction.atomic
def capture_drift(
    *,
    tenant_id: str,
    deployment_id: str,
    window_start: Any,
    window_end: Any,
    metric_kind: str,
    score: Decimal,
    threshold: Decimal = Decimal("0.05"),
    details: dict[str, Any] | None = None,
) -> DriftMetric:
    score_value = Decimal(str(score))
    threshold_value = Decimal(str(threshold))
    breach = score_value > threshold_value
    payload: dict[str, Any] = dict(details or {})
    if breach and metric_kind == DriftMetric.MetricKind.PERFORMANCE_DRIFT:
        payload["suggested_action"] = "retire"
    metric = DriftMetric.objects.create(
        tenant_id=tenant_id,
        deployment_id=deployment_id,
        window_start=window_start,
        window_end=window_end,
        metric_kind=metric_kind,
        score=score_value,
        threshold=threshold_value,
        breach=breach,
        details=payload,
        captured_at=timezone.now(),
    )
    return metric


@transaction.atomic
def open_review_queue(
    *,
    tenant_id: str,
    code: str,
    name: str,
    trigger_rules: dict[str, Any] | None = None,
    priority: int = 100,
) -> HitlReviewQueue:
    queue, _created = HitlReviewQueue.objects.update_or_create(
        tenant_id=tenant_id,
        code=code,
        defaults={
            "name": name,
            "trigger_rules": trigger_rules or {},
            "priority": int(priority),
            "active": True,
        },
    )
    return queue


@transaction.atomic
def enqueue_review(
    *,
    queue_id: str,
    inference_run_id: str,
    study_instance_uid: str,
    priority: str = "routine",
) -> HitlReviewItem:
    item = HitlReviewItem.objects.create(
        queue_id=queue_id,
        inference_run_id=inference_run_id,
        study_instance_uid=study_instance_uid,
        priority=priority,
        status=HitlReviewItem.Status.PENDING,
        created_at=timezone.now(),
    )
    return item


@transaction.atomic
def assign_review(
    *,
    item_id: str,
    reviewer_profile_id: str,
) -> HitlReviewItem:
    item = HitlReviewItem.objects.get(id=item_id)
    item.assigned_reviewer_id = reviewer_profile_id
    item.status = HitlReviewItem.Status.ASSIGNED
    item.save(
        update_fields=["assigned_reviewer_id", "status", "updated_at"]
    )
    return item


@transaction.atomic
def resolve_review(
    *,
    item_id: str,
    status: str,
    override_kind: str = "",
    override_reason: str = "",
) -> HitlReviewItem:
    allowed = {
        HitlReviewItem.Status.ACCEPTED,
        HitlReviewItem.Status.OVERRIDDEN,
        HitlReviewItem.Status.NO_CHANGE,
        HitlReviewItem.Status.ESCALATED,
        HitlReviewItem.Status.EXPIRED,
    }
    if status not in allowed:
        raise ValueError(f"invalid resolution status: {status}")
    item = HitlReviewItem.objects.get(id=item_id)
    item.status = status
    item.override_kind = override_kind
    item.override_reason = override_reason
    item.reviewed_at = timezone.now()
    item.save(
        update_fields=[
            "status",
            "override_kind",
            "override_reason",
            "reviewed_at",
            "updated_at",
        ]
    )
    return item


def _extract_baseline(note: str) -> Decimal:
    if not note:
        return DEFAULT_BASELINE_SENSITIVITY
    import json

    try:
        payload = json.loads(note)
    except (ValueError, TypeError):
        return DEFAULT_BASELINE_SENSITIVITY
    if isinstance(payload, dict):
        baseline = payload.get("baseline_sensitivity")
        if baseline is not None:
            try:
                return Decimal(str(baseline))
            except (ValueError, TypeError):
                return DEFAULT_BASELINE_SENSITIVITY
    return DEFAULT_BASELINE_SENSITIVITY


@transaction.atomic
def record_bias_audit(
    *,
    tenant_id: str,
    ai_model_id: str,
    version: str = "",
    cohort_kind: str,
    cohort_value: str = "",
    sample_size: int = 0,
    auc: Decimal | None = None,
    sensitivity: Decimal | None = None,
    specificity: Decimal | None = None,
    false_positive_rate: Decimal | None = None,
    false_negative_rate: Decimal | None = None,
    note: str = "",
) -> BiasAudit:
    baseline = _extract_baseline(note)
    equity_flag = False
    if sensitivity is not None:
        cohort_sens = Decimal(str(sensitivity))
        if abs(cohort_sens - baseline) > EQUITY_DELTA_THRESHOLD:
            equity_flag = True
    audit = BiasAudit.objects.create(
        tenant_id=tenant_id,
        ai_model_id=ai_model_id,
        version=version,
        cohort_kind=cohort_kind,
        cohort_value=cohort_value,
        sample_size=int(sample_size),
        auc=None if auc is None else Decimal(str(auc)),
        sensitivity=None if sensitivity is None else Decimal(str(sensitivity)),
        specificity=None if specificity is None else Decimal(str(specificity)),
        false_positive_rate=(
            None if false_positive_rate is None else Decimal(str(false_positive_rate))
        ),
        false_negative_rate=(
            None if false_negative_rate is None else Decimal(str(false_negative_rate))
        ),
        equity_flag=equity_flag,
        captured_at=timezone.now(),
        note=note,
    )
    return audit
