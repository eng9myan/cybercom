"""Data models for CyMed MRFF population health, registries and analytics."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class Registry(BaseModel):
    class Kind(models.TextChoices):
        CHRONIC_DISEASE = "chronic_disease", "Chronic Disease"
        CANCER = "cancer", "Cancer"
        CARDIAC = "cardiac", "Cardiac"
        DIABETES = "diabetes", "Diabetes"
        RARE_DISEASE = "rare_disease", "Rare Disease"
        INFECTIOUS = "infectious", "Infectious"
        IMMUNISATION = "immunisation", "Immunisation"
        MATERNAL_CHILD = "maternal_child", "Maternal & Child"
        MENTAL_HEALTH = "mental_health", "Mental Health"
        TRAUMA = "trauma", "Trauma"
        RENAL = "renal", "Renal"

    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    icd_codes = models.JSONField(default=list)
    inclusion_rules = models.JSONField(default=dict)
    stewards = models.JSONField(default=list)
    consent_required = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_mrff_population_health_registry"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"Registry<{self.code}:{self.name}>"


class RegistryCase(BaseModel):
    class Status(models.TextChoices):
        CANDIDATE = "candidate", "Candidate"
        ENROLLED = "enrolled", "Enrolled"
        ACTIVE = "active", "Active"
        REMISSION = "remission", "Remission"
        LOST_TO_FOLLOWUP = "lost_to_followup", "Lost to Follow-up"
        DECEASED = "deceased", "Deceased"
        WITHDRAWN = "withdrawn", "Withdrawn"

    registry = models.ForeignKey(
        Registry, on_delete=models.CASCADE, related_name="cases"
    )
    tenant_id = models.UUIDField(db_index=True)
    patient_pseudonym = models.CharField(max_length=64, db_index=True)
    patient_profile_id = models.UUIDField(null=True, blank=True)
    diagnosis_code = models.CharField(max_length=32, blank=True)
    diagnosed_at = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.CANDIDATE
    )
    enrollment_at = models.DateTimeField(default=timezone.now)
    stage_or_grade = models.CharField(max_length=64, blank=True)
    comorbidities = models.JSONField(default=list)
    treatments = models.JSONField(default=list)
    last_updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_population_health_registrycase"
        unique_together = [("registry", "patient_pseudonym")]

    def __str__(self) -> str:
        return f"RegistryCase<{self.registry_id}:{self.patient_pseudonym}>"


class PopulationCohort(BaseModel):
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    inclusion_criteria = models.JSONField(default=dict)
    exclusion_criteria = models.JSONField(default=dict)
    size = models.IntegerField(default=0)
    refreshed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_population_health_populationcohort"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"PopulationCohort<{self.code}:{self.name}>"


class PopulationMetric(BaseModel):
    class MetricKind(models.TextChoices):
        PREVALENCE = "prevalence", "Prevalence"
        INCIDENCE = "incidence", "Incidence"
        MORTALITY = "mortality", "Mortality"
        READMISSION = "readmission", "Readmission"
        HBA1C_CONTROL = "hba1c_control", "HbA1c Control"
        BP_CONTROL = "bp_control", "BP Control"
        VACCINATION_UPTAKE = "vaccination_uptake", "Vaccination Uptake"
        MEDICATION_ADHERENCE = "medication_adherence", "Medication Adherence"
        COST_PMPM = "cost_pmpm", "Cost PMPM"

    cohort = models.ForeignKey(
        PopulationCohort, on_delete=models.CASCADE, related_name="metrics"
    )
    metric_kind = models.CharField(max_length=32, choices=MetricKind.choices)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    denominator = models.IntegerField(default=0)
    period_start = models.DateField()
    period_end = models.DateField()
    computed_at = models.DateTimeField(default=timezone.now)
    breakdowns = models.JSONField(default=dict)

    class Meta:
        db_table = "cymed_mrff_population_health_populationmetric"

    def __str__(self) -> str:
        return f"PopulationMetric<{self.cohort_id}:{self.metric_kind}:{self.value}>"


class OutbreakModel(BaseModel):
    class RegionKind(models.TextChoices):
        CITY = "city", "City"
        GOVERNORATE = "governorate", "Governorate"
        COUNTRY = "country", "Country"
        CROSS_BORDER = "cross_border", "Cross-border"

    class ModelKind(models.TextChoices):
        SIR = "sir", "SIR"
        SEIR = "seir", "SEIR"
        SEIRD = "seird", "SEIRD"
        ABM = "abm", "Agent-based"
        STATISTICAL = "statistical", "Statistical"

    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    pathogen = models.CharField(max_length=64)
    region_kind = models.CharField(max_length=32, choices=RegionKind.choices)
    region_code = models.CharField(max_length=32, blank=True)
    model_kind = models.CharField(
        max_length=32, choices=ModelKind.choices, default=ModelKind.SEIR
    )
    parameters = models.JSONField(default=dict)
    projection_start = models.DateField()
    projection_end = models.DateField()
    peaked_at = models.DateField(null=True, blank=True)
    total_infected_projection = models.IntegerField(default=0)
    total_deceased_projection = models.IntegerField(default=0)
    ran_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_population_health_outbreakmodel"

    def __str__(self) -> str:
        return f"OutbreakModel<{self.pathogen}:{self.region_kind}:{self.region_code}>"


class TreatmentComparator(BaseModel):
    class Method(models.TextChoices):
        PROPENSITY_MATCHED = "propensity_matched", "Propensity Matched"
        REGRESSION_ADJUSTED = "regression_adjusted", "Regression Adjusted"
        INSTRUMENTAL_VAR = "instrumental_var", "Instrumental Variable"
        RCT = "rct", "Randomised Controlled Trial"
        SYNTHETIC_CONTROL = "synthetic_control", "Synthetic Control"

    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    condition_code = models.CharField(max_length=32)
    arm_a = models.CharField(max_length=255)
    arm_b = models.CharField(max_length=255)
    cohort_a = models.ForeignKey(
        PopulationCohort,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    cohort_b = models.ForeignKey(
        PopulationCohort,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    primary_endpoint = models.CharField(max_length=255, blank=True)
    arm_a_outcome_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    arm_b_outcome_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    relative_effect = models.DecimalField(
        max_digits=9, decimal_places=4, null=True, blank=True
    )
    ci_low = models.DecimalField(
        max_digits=9, decimal_places=4, null=True, blank=True
    )
    ci_high = models.DecimalField(
        max_digits=9, decimal_places=4, null=True, blank=True
    )
    p_value = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    method = models.CharField(
        max_length=32, choices=Method.choices, default=Method.PROPENSITY_MATCHED
    )
    ran_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_population_health_treatmentcomparator"

    def __str__(self) -> str:
        return f"TreatmentComparator<{self.condition_code}:{self.arm_a}vs{self.arm_b}>"
