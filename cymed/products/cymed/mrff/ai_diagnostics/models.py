"""Data models for CyMed MRFF diagnostic and imaging AI governance."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class ModelCard(BaseModel):
    class RegulatoryKind(models.TextChoices):
        FDA_CLEARED = "fda_cleared", "FDA Cleared"
        CE_MARKED = "ce_marked", "CE Marked"
        TGA_INCLUDED = "tga_included", "TGA Included"
        SFDA_CLEARED = "sfda_cleared", "SFDA Cleared"
        RESEARCH_ONLY = "research_only", "Research Only"
        UNKNOWN = "unknown", "Unknown"

    tenant_id = models.UUIDField(null=True, blank=True)
    ai_model_id = models.UUIDField(db_index=True)
    intended_use = models.TextField()
    target_population = models.TextField(blank=True)
    clinical_workflow = models.TextField(blank=True)
    inputs_description = models.TextField(blank=True)
    outputs_description = models.TextField(blank=True)
    performance = models.JSONField(default=dict)
    validation_datasets = models.JSONField(default=list)
    known_limitations = models.TextField(blank=True)
    ethical_considerations = models.TextField(blank=True)
    maintainer_email = models.CharField(max_length=255, blank=True)
    regulatory_kind = models.CharField(
        max_length=32,
        choices=RegulatoryKind.choices,
        default=RegulatoryKind.UNKNOWN,
    )
    regulatory_reference = models.CharField(max_length=255, blank=True)
    tga_artg_number = models.CharField(max_length=64, blank=True)
    version = models.CharField(max_length=32)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_mrff_ai_diagnostics_modelcard"
        unique_together = [("ai_model_id", "version")]

    def __str__(self) -> str:
        return f"ModelCard<{self.ai_model_id}:{self.version}>"


class Deployment(BaseModel):
    class Environment(models.TextChoices):
        SHADOW = "shadow", "Shadow"
        CANARY = "canary", "Canary"
        PRODUCTION = "production", "Production"
        RETIRED = "retired", "Retired"

    tenant_id = models.UUIDField(db_index=True)
    ai_model_id = models.UUIDField(db_index=True)
    version = models.CharField(max_length=32)
    environment = models.CharField(
        max_length=32,
        choices=Environment.choices,
        default=Environment.CANARY,
    )
    traffic_percent = models.IntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    rollback_reason = models.TextField(blank=True)
    deployed_by_profile_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_mrff_ai_diagnostics_deployment"

    def __str__(self) -> str:
        return f"Deployment<{self.ai_model_id}:{self.version}:{self.environment}>"


class InferenceOutcome(BaseModel):
    class GroundTruthSource(models.TextChoices):
        RADIOLOGIST_REVIEWED = "radiologist_reviewed", "Radiologist Reviewed"
        GOLD_STANDARD = "gold_standard", "Gold Standard"
        FOLLOW_UP = "follow_up", "Follow-up"
        UNKNOWN = "unknown", "Unknown"

    class Outcome(models.TextChoices):
        TRUE_POSITIVE = "true_positive", "True Positive"
        FALSE_POSITIVE = "false_positive", "False Positive"
        TRUE_NEGATIVE = "true_negative", "True Negative"
        FALSE_NEGATIVE = "false_negative", "False Negative"
        UNKNOWN = "unknown", "Unknown"

    deployment = models.ForeignKey(
        Deployment, on_delete=models.CASCADE, related_name="outcomes"
    )
    study_instance_uid = models.CharField(max_length=128, db_index=True)
    inference_run_id = models.UUIDField(null=True, blank=True)
    predicted_kind = models.CharField(max_length=64, blank=True)
    predicted_confidence = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0")
    )
    ground_truth_kind = models.CharField(max_length=64, blank=True)
    ground_truth_source = models.CharField(
        max_length=32,
        choices=GroundTruthSource.choices,
        default=GroundTruthSource.UNKNOWN,
    )
    outcome = models.CharField(
        max_length=32,
        choices=Outcome.choices,
        default=Outcome.UNKNOWN,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_profile_id = models.UUIDField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_mrff_ai_diagnostics_inferenceoutcome"

    def __str__(self) -> str:
        return f"InferenceOutcome<{self.study_instance_uid}:{self.outcome}>"


class DriftMetric(BaseModel):
    class MetricKind(models.TextChoices):
        INPUT_DRIFT = "input_drift", "Input Drift"
        PREDICTION_DRIFT = "prediction_drift", "Prediction Drift"
        PERFORMANCE_DRIFT = "performance_drift", "Performance Drift"
        CALIBRATION_DRIFT = "calibration_drift", "Calibration Drift"
        DATA_QUALITY = "data_quality", "Data Quality"

    tenant_id = models.UUIDField(db_index=True)
    deployment = models.ForeignKey(
        Deployment, on_delete=models.CASCADE, related_name="drift_metrics"
    )
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    metric_kind = models.CharField(max_length=32, choices=MetricKind.choices)
    score = models.DecimalField(max_digits=9, decimal_places=6)
    threshold = models.DecimalField(
        max_digits=9, decimal_places=6, default=Decimal("0.05")
    )
    breach = models.BooleanField(default=False)
    details = models.JSONField(default=dict)
    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_ai_diagnostics_driftmetric"

    def __str__(self) -> str:
        return f"DriftMetric<{self.deployment_id}:{self.metric_kind}:{self.score}>"


class HitlReviewQueue(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    trigger_rules = models.JSONField(default=dict)
    priority = models.IntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_mrff_ai_diagnostics_hitlreviewqueue"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"HitlReviewQueue<{self.code}:{self.name}>"


class HitlReviewItem(BaseModel):
    class Priority(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ASSIGNED = "assigned", "Assigned"
        ACCEPTED = "accepted", "Accepted"
        OVERRIDDEN = "overridden", "Overridden"
        NO_CHANGE = "no_change", "No Change"
        ESCALATED = "escalated", "Escalated"
        EXPIRED = "expired", "Expired"

    queue = models.ForeignKey(
        HitlReviewQueue, on_delete=models.CASCADE, related_name="items"
    )
    inference_run_id = models.UUIDField(db_index=True)
    study_instance_uid = models.CharField(max_length=128, db_index=True)
    priority = models.CharField(
        max_length=32,
        choices=Priority.choices,
        default=Priority.ROUTINE,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    assigned_reviewer_id = models.UUIDField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    override_kind = models.CharField(max_length=64, blank=True)
    override_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_ai_diagnostics_hitlreviewitem"

    def __str__(self) -> str:
        return f"HitlReviewItem<{self.study_instance_uid}:{self.status}>"


class BiasAudit(BaseModel):
    class CohortKind(models.TextChoices):
        SEX = "sex", "Sex"
        AGE_GROUP = "age_group", "Age Group"
        ETHNICITY = "ethnicity", "Ethnicity"
        SOCIOECONOMIC = "socioeconomic", "Socioeconomic"
        GEOGRAPHIC = "geographic", "Geographic"
        LANGUAGE = "language", "Language"
        EQUIPMENT_VENDOR = "equipment_vendor", "Equipment Vendor"

    tenant_id = models.UUIDField(db_index=True)
    ai_model_id = models.UUIDField(db_index=True)
    version = models.CharField(max_length=32, blank=True)
    cohort_kind = models.CharField(max_length=32, choices=CohortKind.choices)
    cohort_value = models.CharField(max_length=64, blank=True)
    sample_size = models.IntegerField(default=0)
    auc = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    sensitivity = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    specificity = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    false_positive_rate = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    false_negative_rate = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    equity_flag = models.BooleanField(default=False)
    captured_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_mrff_ai_diagnostics_biasaudit"

    def __str__(self) -> str:
        return f"BiasAudit<{self.ai_model_id}:{self.cohort_kind}:{self.cohort_value}>"
