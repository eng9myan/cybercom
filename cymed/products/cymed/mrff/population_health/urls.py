"""URL routes for CyMed MRFF population health API."""
from __future__ import annotations

from django.urls import path

from .views import (
    OutbreakModelViewSet,
    PopulationCohortViewSet,
    PopulationMetricViewSet,
    RegistryCaseViewSet,
    RegistryViewSet,
    TreatmentComparatorViewSet,
)

registry_list = RegistryViewSet.as_view({"get": "list", "post": "create"})
registry_detail = RegistryViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
registry_create_action = RegistryViewSet.as_view({"post": "create_registry"})

case_list = RegistryCaseViewSet.as_view({"get": "list", "post": "create"})
case_detail = RegistryCaseViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
case_enrol = RegistryCaseViewSet.as_view({"post": "enrol"})
case_update = RegistryCaseViewSet.as_view({"post": "update_case"})

cohort_list = PopulationCohortViewSet.as_view({"get": "list", "post": "create"})
cohort_detail = PopulationCohortViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
cohort_define = PopulationCohortViewSet.as_view({"post": "define_cohort"})
cohort_refresh = PopulationCohortViewSet.as_view({"post": "refresh_size"})

metric_list = PopulationMetricViewSet.as_view({"get": "list", "post": "create"})
metric_detail = PopulationMetricViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
metric_compute = PopulationMetricViewSet.as_view({"post": "compute_metric"})

outbreak_list = OutbreakModelViewSet.as_view({"get": "list", "post": "create"})
outbreak_detail = OutbreakModelViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
outbreak_run = OutbreakModelViewSet.as_view({"post": "run_outbreak_model"})

comparator_list = TreatmentComparatorViewSet.as_view({"get": "list", "post": "create"})
comparator_detail = TreatmentComparatorViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
comparator_compare = TreatmentComparatorViewSet.as_view({"post": "compare_treatments"})

urlpatterns = [
    path("registries/", registry_list, name="ph-registry-list"),
    path("registries/create-registry/", registry_create_action, name="ph-registry-create-action"),
    path("registries/<uuid:pk>/", registry_detail, name="ph-registry-detail"),
    path("cases/", case_list, name="ph-case-list"),
    path("cases/enrol/", case_enrol, name="ph-case-enrol"),
    path("cases/<uuid:pk>/", case_detail, name="ph-case-detail"),
    path("cases/<uuid:pk>/update-case/", case_update, name="ph-case-update"),
    path("cohorts/", cohort_list, name="ph-cohort-list"),
    path("cohorts/define-cohort/", cohort_define, name="ph-cohort-define"),
    path("cohorts/<uuid:pk>/", cohort_detail, name="ph-cohort-detail"),
    path("cohorts/<uuid:pk>/refresh-size/", cohort_refresh, name="ph-cohort-refresh"),
    path("metrics/", metric_list, name="ph-metric-list"),
    path("metrics/compute-metric/", metric_compute, name="ph-metric-compute"),
    path("metrics/<uuid:pk>/", metric_detail, name="ph-metric-detail"),
    path("outbreaks/", outbreak_list, name="ph-outbreak-list"),
    path("outbreaks/run-outbreak-model/", outbreak_run, name="ph-outbreak-run"),
    path("outbreaks/<uuid:pk>/", outbreak_detail, name="ph-outbreak-detail"),
    path("comparators/", comparator_list, name="ph-comparator-list"),
    path("comparators/compare-treatments/", comparator_compare, name="ph-comparator-compare"),
    path("comparators/<uuid:pk>/", comparator_detail, name="ph-comparator-detail"),
]
