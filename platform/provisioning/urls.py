from django.urls import path
from rest_framework.routers import DefaultRouter

from platform.provisioning.views import (
    AIProposalView,
    CompanyBlueprintViewSet,
    CountryPackViewSet,
    DepartmentPackViewSet,
    IndustryTemplateViewSet,
    TenantConfigParameterViewSet,
)

router = DefaultRouter()
router.register("country-packs", CountryPackViewSet, basename="country-pack")
router.register("department-packs", DepartmentPackViewSet, basename="department-pack")
router.register("industry-templates", IndustryTemplateViewSet, basename="industry-template")
router.register("blueprints", CompanyBlueprintViewSet, basename="company-blueprint")
router.register("config-parameters", TenantConfigParameterViewSet, basename="config-parameter")

urlpatterns = [
    path("ai-propose/", AIProposalView.as_view(), name="ai-propose"),
] + router.urls
