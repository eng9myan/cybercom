"""Service layer for CyMed Imaging AI triage: registry, dispatch, adapters, alerts."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import AiModel, InferenceRun, TriageAlert, TriageFinding, TriageQueue


_DEFAULT_STUB_FINDINGS: list[dict[str, Any]] = [
    {
        "finding_kind": "normal",
        "severity": "normal",
        "confidence": Decimal("0.99"),
        "bbox": {},
        "raw": {},
    }
]


def _adapter_aidoc_infer(run: InferenceRun) -> tuple[bool, list[dict[str, Any]], dict[str, Any], int, str]:
    return (True, list(_DEFAULT_STUB_FINDINGS), {}, 250, "")


def _adapter_rapid_infer(run: InferenceRun) -> tuple[bool, list[dict[str, Any]], dict[str, Any], int, str]:
    return (True, list(_DEFAULT_STUB_FINDINGS), {}, 250, "")


def _adapter_viz_infer(run: InferenceRun) -> tuple[bool, list[dict[str, Any]], dict[str, Any], int, str]:
    return (True, list(_DEFAULT_STUB_FINDINGS), {}, 250, "")


def _adapter_zebra_infer(run: InferenceRun) -> tuple[bool, list[dict[str, Any]], dict[str, Any], int, str]:
    return (True, list(_DEFAULT_STUB_FINDINGS), {}, 250, "")


def _adapter_annalise_infer(run: InferenceRun) -> tuple[bool, list[dict[str, Any]], dict[str, Any], int, str]:
    return (True, list(_DEFAULT_STUB_FINDINGS), {}, 250, "")


def _adapter_lunit_infer(run: InferenceRun) -> tuple[bool, list[dict[str, Any]], dict[str, Any], int, str]:
    return (True, list(_DEFAULT_STUB_FINDINGS), {}, 250, "")


def _adapter_generic_infer(run: InferenceRun) -> tuple[bool, list[dict[str, Any]], dict[str, Any], int, str]:
    return (True, list(_DEFAULT_STUB_FINDINGS), {}, 250, "")


_ADAPTER_ROUTES = {
    "aidoc": _adapter_aidoc_infer,
    "rapid": _adapter_rapid_infer,
    "viz": _adapter_viz_infer,
    "zebra": _adapter_zebra_infer,
    "annalise": _adapter_annalise_infer,
    "lunit": _adapter_lunit_infer,
}


def _resolve_adapter(vendor: str):
    key = (vendor or "").strip().lower()
    return _ADAPTER_ROUTES.get(key, _adapter_generic_infer)


def _classify_priority(rules: dict[str, Any], finding_kind: str, severity: str) -> str:
    rules = rules or {}
    critical_kinds = set(rules.get("critical", []) or [])
    urgent_kinds = set(rules.get("urgent", []) or [])
    if finding_kind in critical_kinds or severity == "critical":
        return TriageAlert.Priority.CRITICAL.value
    if finding_kind in urgent_kinds or severity == "high":
        return TriageAlert.Priority.URGENT.value
    return TriageAlert.Priority.ROUTINE.value


@transaction.atomic
def register_model(
    *,
    vendor: str,
    product_code: str,
    version: str,
    modality: str,
    body_part: str = "",
    finding_kinds: list[str],
    regulatory_kind: str,
    regulatory_reference: str = "",
    endpoint_url: str = "",
    auth_kind: str = "none",
    auth_secret_ref: str = "",
    tenant_id: Any = None,
) -> AiModel:
    model, _ = AiModel.objects.update_or_create(
        vendor=vendor,
        product_code=product_code,
        version=version,
        defaults={
            "tenant_id": tenant_id,
            "modality": modality,
            "body_part": body_part,
            "finding_kinds": list(finding_kinds or []),
            "regulatory_kind": regulatory_kind,
            "regulatory_reference": regulatory_reference,
            "endpoint_url": endpoint_url,
            "auth_kind": auth_kind,
            "auth_secret_ref": auth_secret_ref,
            "enabled": True,
        },
    )
    return model


@transaction.atomic
def open_queue(
    *,
    tenant_id: Any,
    code: str,
    name: str,
    modality: str,
    priority_rules: dict[str, Any] | None = None,
) -> TriageQueue:
    queue, _ = TriageQueue.objects.update_or_create(
        tenant_id=tenant_id,
        code=code,
        defaults={
            "name": name,
            "modality": modality,
            "priority_rules": dict(priority_rules or {}),
            "active": True,
        },
    )
    return queue


@transaction.atomic
def request_inference(
    *,
    tenant_id: Any,
    model_id: Any,
    study_instance_uid: str,
    ordered_by_profile_id: Any = None,
) -> InferenceRun:
    model = AiModel.objects.get(pk=model_id)
    run = InferenceRun.objects.create(
        tenant_id=tenant_id,
        model=model,
        study_instance_uid=study_instance_uid,
        ordered_by_profile_id=ordered_by_profile_id,
        status=InferenceRun.Status.QUEUED,
        requested_at=timezone.now(),
    )
    return run


@transaction.atomic
def dispatch_run(*, run_id: Any) -> InferenceRun:
    run = InferenceRun.objects.select_for_update().select_related("model").get(pk=run_id)
    run.status = InferenceRun.Status.RUNNING
    run.started_at = timezone.now()
    run.save(update_fields=["status", "started_at"])

    adapter = _resolve_adapter(run.model.vendor)
    ok, findings_list, raw_payload, latency_ms, err = adapter(run)

    run.raw_response = raw_payload or {}
    run.latency_ms = int(latency_ms or 0)
    run.completed_at = timezone.now()

    if not ok:
        run.status = InferenceRun.Status.FAILED
        run.error_message = err or ""
        run.save(
            update_fields=[
                "raw_response",
                "latency_ms",
                "completed_at",
                "status",
                "error_message",
            ]
        )
        return run

    run.status = InferenceRun.Status.COMPLETED
    run.error_message = ""
    run.save(
        update_fields=[
            "raw_response",
            "latency_ms",
            "completed_at",
            "status",
            "error_message",
        ]
    )

    created_findings: list[TriageFinding] = []
    high_or_critical: list[TriageFinding] = []
    for entry in findings_list or []:
        severity = str(entry.get("severity") or "normal")
        finding_kind = str(entry.get("finding_kind") or "unknown")
        confidence_raw = entry.get("confidence", Decimal("0"))
        try:
            confidence = Decimal(str(confidence_raw))
        except Exception:
            confidence = Decimal("0")
        finding = TriageFinding.objects.create(
            run=run,
            finding_kind=finding_kind,
            severity=severity,
            confidence=confidence,
            bbox=dict(entry.get("bbox") or {}),
            raw=dict(entry.get("raw") or {}),
        )
        created_findings.append(finding)
        if severity in {"high", "critical"}:
            high_or_critical.append(finding)

    if high_or_critical:
        candidate_queues = TriageQueue.objects.filter(
            tenant_id=run.tenant_id,
            modality=run.model.modality,
            active=True,
        )
        for finding in high_or_critical:
            matched_queue: TriageQueue | None = None
            for queue in candidate_queues:
                rules = queue.priority_rules or {}
                kinds_all: set[str] = set()
                for _bucket, kinds in rules.items():
                    if isinstance(kinds, (list, tuple)):
                        kinds_all.update(kinds)
                if not kinds_all or finding.finding_kind in kinds_all:
                    matched_queue = queue
                    break
            if matched_queue is None:
                continue
            priority = _classify_priority(
                matched_queue.priority_rules or {},
                finding.finding_kind,
                finding.severity,
            )
            TriageAlert.objects.create(
                tenant_id=run.tenant_id,
                queue=matched_queue,
                run=run,
                study_instance_uid=run.study_instance_uid,
                priority=priority,
                finding_kind=finding.finding_kind,
                status=TriageAlert.Status.OPEN,
            )

    return run


@transaction.atomic
def acknowledge_alert(*, alert_id: Any, radiologist_profile_id: Any) -> TriageAlert:
    alert = TriageAlert.objects.select_for_update().get(pk=alert_id)
    alert.status = TriageAlert.Status.ACKNOWLEDGED
    alert.assigned_radiologist_id = radiologist_profile_id
    alert.acknowledged_at = timezone.now()
    alert.save(update_fields=["status", "assigned_radiologist_id", "acknowledged_at"])
    return alert


@transaction.atomic
def dismiss_alert(*, alert_id: Any, reason: str) -> TriageAlert:
    alert = TriageAlert.objects.select_for_update().get(pk=alert_id)
    alert.status = TriageAlert.Status.DISMISSED
    alert.dismissed_reason = reason or ""
    alert.save(update_fields=["status", "dismissed_reason"])
    return alert


@transaction.atomic
def escalate_alert(*, alert_id: Any, escalate_to_profile_id: Any) -> TriageAlert:
    alert = TriageAlert.objects.select_for_update().get(pk=alert_id)
    alert.status = TriageAlert.Status.ESCALATED
    alert.assigned_radiologist_id = escalate_to_profile_id
    alert.save(update_fields=["status", "assigned_radiologist_id"])
    return alert
