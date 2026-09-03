"""Service functions implementing CyMed MRFF population health flows."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from .models import (
    OutbreakModel,
    PopulationCohort,
    PopulationMetric,
    Registry,
    RegistryCase,
    TreatmentComparator,
)


@transaction.atomic
def create_registry(
    *,
    code: str,
    name: str,
    kind: str,
    icd_codes: list,
    inclusion_rules: Optional[dict] = None,
    name_ar: str = "",
    stewards: Optional[list] = None,
    consent_required: bool = True,
    tenant_id: Optional[UUID] = None,
) -> Registry:
    return Registry.objects.create(
        tenant_id=tenant_id,
        code=code,
        name=name,
        name_ar=name_ar,
        kind=kind,
        icd_codes=list(icd_codes or []),
        inclusion_rules=dict(inclusion_rules or {}),
        stewards=list(stewards or []),
        consent_required=consent_required,
        active=True,
    )


@transaction.atomic
def enrol_case(
    *,
    registry_id: UUID,
    tenant_id: UUID,
    patient_pseudonym: str,
    patient_profile_id: Optional[UUID] = None,
    diagnosis_code: str = "",
    diagnosed_at: Optional[date] = None,
    stage_or_grade: str = "",
    comorbidities: Optional[list] = None,
    treatments: Optional[list] = None,
) -> RegistryCase:
    return RegistryCase.objects.create(
        registry_id=registry_id,
        tenant_id=tenant_id,
        patient_pseudonym=patient_pseudonym,
        patient_profile_id=patient_profile_id,
        diagnosis_code=diagnosis_code,
        diagnosed_at=diagnosed_at,
        status=RegistryCase.Status.ENROLLED,
        enrollment_at=timezone.now(),
        stage_or_grade=stage_or_grade,
        comorbidities=list(comorbidities or []),
        treatments=list(treatments or []),
        last_updated_at=timezone.now(),
    )


@transaction.atomic
def update_case(
    *,
    case_id: UUID,
    status: Optional[str] = None,
    stage_or_grade: Optional[str] = None,
    comorbidities: Optional[list] = None,
    treatments: Optional[list] = None,
) -> RegistryCase:
    case = RegistryCase.objects.select_for_update().get(pk=case_id)
    if status is not None:
        case.status = status
    if stage_or_grade is not None:
        case.stage_or_grade = stage_or_grade
    if comorbidities is not None:
        case.comorbidities = list(comorbidities)
    if treatments is not None:
        case.treatments = list(treatments)
    case.last_updated_at = timezone.now()
    case.save()
    return case


@transaction.atomic
def define_cohort(
    *,
    tenant_id: Optional[UUID],
    code: str,
    name: str,
    description: str = "",
    inclusion_criteria: Optional[dict] = None,
    exclusion_criteria: Optional[dict] = None,
) -> PopulationCohort:
    return PopulationCohort.objects.create(
        tenant_id=tenant_id,
        code=code,
        name=name,
        description=description,
        inclusion_criteria=dict(inclusion_criteria or {}),
        exclusion_criteria=dict(exclusion_criteria or {}),
        size=0,
        refreshed_at=timezone.now(),
    )


@transaction.atomic
def refresh_cohort_size(*, cohort_id: UUID, size: int) -> PopulationCohort:
    cohort = PopulationCohort.objects.select_for_update().get(pk=cohort_id)
    cohort.size = int(size)
    cohort.refreshed_at = timezone.now()
    cohort.save()
    return cohort


@transaction.atomic
def compute_metric(
    *,
    cohort_id: UUID,
    metric_kind: str,
    value: Any,
    denominator: int,
    period_start: date,
    period_end: date,
    breakdowns: Optional[dict] = None,
) -> PopulationMetric:
    return PopulationMetric.objects.create(
        cohort_id=cohort_id,
        metric_kind=metric_kind,
        value=Decimal(str(value)),
        denominator=int(denominator),
        period_start=period_start,
        period_end=period_end,
        computed_at=timezone.now(),
        breakdowns=dict(breakdowns or {}),
    )


@transaction.atomic
def run_outbreak_model(
    *,
    tenant_id: Optional[UUID],
    pathogen: str,
    region_kind: str,
    region_code: str = "",
    model_kind: str = "seir",
    parameters: dict,
    projection_start: date,
    projection_end: date,
    peaked_at: Optional[date] = None,
    total_infected_projection: int = 0,
    total_deceased_projection: int = 0,
) -> OutbreakModel:
    return OutbreakModel.objects.create(
        tenant_id=tenant_id,
        pathogen=pathogen,
        region_kind=region_kind,
        region_code=region_code,
        model_kind=model_kind,
        parameters=dict(parameters or {}),
        projection_start=projection_start,
        projection_end=projection_end,
        peaked_at=peaked_at,
        total_infected_projection=int(total_infected_projection),
        total_deceased_projection=int(total_deceased_projection),
        ran_at=timezone.now(),
    )


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


@transaction.atomic
def compare_treatments(
    *,
    tenant_id: Optional[UUID],
    condition_code: str,
    arm_a: str,
    arm_b: str,
    cohort_a_id: Optional[UUID] = None,
    cohort_b_id: Optional[UUID] = None,
    primary_endpoint: str = "",
    arm_a_outcome_value: Any = None,
    arm_b_outcome_value: Any = None,
    relative_effect: Any = None,
    ci_low: Any = None,
    ci_high: Any = None,
    p_value: Any = None,
    method: str = "propensity_matched",
) -> TreatmentComparator:
    return TreatmentComparator.objects.create(
        tenant_id=tenant_id,
        condition_code=condition_code,
        arm_a=arm_a,
        arm_b=arm_b,
        cohort_a_id=cohort_a_id,
        cohort_b_id=cohort_b_id,
        primary_endpoint=primary_endpoint,
        arm_a_outcome_value=_to_decimal(arm_a_outcome_value),
        arm_b_outcome_value=_to_decimal(arm_b_outcome_value),
        relative_effect=_to_decimal(relative_effect),
        ci_low=_to_decimal(ci_low),
        ci_high=_to_decimal(ci_high),
        p_value=_to_decimal(p_value),
        method=method,
        ran_at=timezone.now(),
    )
