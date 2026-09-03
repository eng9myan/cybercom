"""API viewsets for CyMed MRFF population health sub-app."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    OutbreakModel,
    PopulationCohort,
    PopulationMetric,
    Registry,
    RegistryCase,
    TreatmentComparator,
)
from .serializers import (
    OutbreakModelSerializer,
    PopulationCohortSerializer,
    PopulationMetricSerializer,
    RegistryCaseSerializer,
    RegistrySerializer,
    TreatmentComparatorSerializer,
)


class RegistryViewSet(viewsets.ModelViewSet):
    queryset = Registry.objects.all()
    serializer_class = RegistrySerializer

    @action(detail=False, methods=["post"], url_path="create-registry")
    def create_registry(self, request):
        data = request.data
        registry = services.create_registry(
            code=data["code"],
            name=data["name"],
            kind=data["kind"],
            icd_codes=data.get("icd_codes", []),
            inclusion_rules=data.get("inclusion_rules"),
            name_ar=data.get("name_ar", ""),
            stewards=data.get("stewards"),
            consent_required=data.get("consent_required", True),
            tenant_id=data.get("tenant_id"),
        )
        return Response(RegistrySerializer(registry).data)


class RegistryCaseViewSet(viewsets.ModelViewSet):
    queryset = RegistryCase.objects.all()
    serializer_class = RegistryCaseSerializer

    @action(detail=False, methods=["post"], url_path="enrol")
    def enrol(self, request):
        data = request.data
        case = services.enrol_case(
            registry_id=data["registry_id"],
            tenant_id=data["tenant_id"],
            patient_pseudonym=data["patient_pseudonym"],
            patient_profile_id=data.get("patient_profile_id"),
            diagnosis_code=data.get("diagnosis_code", ""),
            diagnosed_at=data.get("diagnosed_at"),
            stage_or_grade=data.get("stage_or_grade", ""),
            comorbidities=data.get("comorbidities"),
            treatments=data.get("treatments"),
        )
        return Response(RegistryCaseSerializer(case).data)

    @action(detail=True, methods=["post"], url_path="update-case")
    def update_case(self, request, pk=None):
        data = request.data
        case = services.update_case(
            case_id=pk,
            status=data.get("status"),
            stage_or_grade=data.get("stage_or_grade"),
            comorbidities=data.get("comorbidities"),
            treatments=data.get("treatments"),
        )
        return Response(RegistryCaseSerializer(case).data)


class PopulationCohortViewSet(viewsets.ModelViewSet):
    queryset = PopulationCohort.objects.all()
    serializer_class = PopulationCohortSerializer

    @action(detail=False, methods=["post"], url_path="define-cohort")
    def define_cohort(self, request):
        data = request.data
        cohort = services.define_cohort(
            tenant_id=data.get("tenant_id"),
            code=data["code"],
            name=data["name"],
            description=data.get("description", ""),
            inclusion_criteria=data.get("inclusion_criteria"),
            exclusion_criteria=data.get("exclusion_criteria"),
        )
        return Response(PopulationCohortSerializer(cohort).data)

    @action(detail=True, methods=["post"], url_path="refresh-size")
    def refresh_size(self, request, pk=None):
        data = request.data
        cohort = services.refresh_cohort_size(cohort_id=pk, size=int(data["size"]))
        return Response(PopulationCohortSerializer(cohort).data)


class PopulationMetricViewSet(viewsets.ModelViewSet):
    queryset = PopulationMetric.objects.all()
    serializer_class = PopulationMetricSerializer

    @action(detail=False, methods=["post"], url_path="compute-metric")
    def compute_metric(self, request):
        data = request.data
        metric = services.compute_metric(
            cohort_id=data["cohort_id"],
            metric_kind=data["metric_kind"],
            value=data["value"],
            denominator=int(data.get("denominator", 0)),
            period_start=data["period_start"],
            period_end=data["period_end"],
            breakdowns=data.get("breakdowns"),
        )
        return Response(PopulationMetricSerializer(metric).data)


class OutbreakModelViewSet(viewsets.ModelViewSet):
    queryset = OutbreakModel.objects.all()
    serializer_class = OutbreakModelSerializer

    @action(detail=False, methods=["post"], url_path="run-outbreak-model")
    def run_outbreak_model(self, request):
        data = request.data
        outbreak = services.run_outbreak_model(
            tenant_id=data.get("tenant_id"),
            pathogen=data["pathogen"],
            region_kind=data["region_kind"],
            region_code=data.get("region_code", ""),
            model_kind=data.get("model_kind", "seir"),
            parameters=data.get("parameters", {}),
            projection_start=data["projection_start"],
            projection_end=data["projection_end"],
            peaked_at=data.get("peaked_at"),
            total_infected_projection=int(data.get("total_infected_projection", 0)),
            total_deceased_projection=int(data.get("total_deceased_projection", 0)),
        )
        return Response(OutbreakModelSerializer(outbreak).data)


class TreatmentComparatorViewSet(viewsets.ModelViewSet):
    queryset = TreatmentComparator.objects.all()
    serializer_class = TreatmentComparatorSerializer

    @action(detail=False, methods=["post"], url_path="compare-treatments")
    def compare_treatments(self, request):
        data = request.data
        comparator = services.compare_treatments(
            tenant_id=data.get("tenant_id"),
            condition_code=data["condition_code"],
            arm_a=data["arm_a"],
            arm_b=data["arm_b"],
            cohort_a_id=data.get("cohort_a_id"),
            cohort_b_id=data.get("cohort_b_id"),
            primary_endpoint=data.get("primary_endpoint", ""),
            arm_a_outcome_value=data.get("arm_a_outcome_value"),
            arm_b_outcome_value=data.get("arm_b_outcome_value"),
            relative_effect=data.get("relative_effect"),
            ci_low=data.get("ci_low"),
            ci_high=data.get("ci_high"),
            p_value=data.get("p_value"),
            method=data.get("method", "propensity_matched"),
        )
        return Response(TreatmentComparatorSerializer(comparator).data)
