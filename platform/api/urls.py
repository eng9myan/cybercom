"""
API Framework URL configuration. Flat DefaultRouter only (no nested routers).
FHIR: /fhir/{version}/{resource}/ and /fhir/{version}/{resource}/{id}/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ApiApplicationViewSet,
    ApiCatalogViewSet,
    ApiContractViewSet,
    ApiKeyViewSet,
    ApiMetricsView,
    ApiPolicyViewSet,
    ApiRateLimitViewSet,
    ApiSubscriptionViewSet,
    ApiUsageViewSet,
    ApiVersionViewSet,
    ApiWebhookViewSet,
    FHIRResourceView,
    IdempotencyKeyViewSet,
    OpenAPISpecView,
    SDKGenerateView,
)

router = DefaultRouter()
router.register(r"versions", ApiVersionViewSet, basename="api-version")
router.register(r"catalog", ApiCatalogViewSet, basename="api-catalog")
router.register(r"applications", ApiApplicationViewSet, basename="api-application")
router.register(r"keys", ApiKeyViewSet, basename="api-key")
router.register(r"subscriptions", ApiSubscriptionViewSet, basename="api-subscription")
router.register(r"rate-limits", ApiRateLimitViewSet, basename="api-rate-limit")
router.register(r"policies", ApiPolicyViewSet, basename="api-policy")
router.register(r"contracts", ApiContractViewSet, basename="api-contract")
router.register(r"usage", ApiUsageViewSet, basename="api-usage")
router.register(r"webhooks", ApiWebhookViewSet, basename="api-webhook")
router.register(r"idempotency-keys", IdempotencyKeyViewSet, basename="idempotency-key")

fhir_urlpatterns = [
    path(
        "fhir/<str:fhir_version>/<str:resource_type>/",
        FHIRResourceView.as_view(),
        name="fhir-resource-list",
    ),
    path(
        "fhir/<str:fhir_version>/<str:resource_type>/<str:resource_id>/",
        FHIRResourceView.as_view(),
        name="fhir-resource-detail",
    ),
]

urlpatterns = [
    path("", include(router.urls)),
    path("openapi/", OpenAPISpecView.as_view(), name="openapi-root"),
    path("openapi/<slug:catalog_slug>/", OpenAPISpecView.as_view(), name="openapi-catalog"),
    path("sdk/generate/", SDKGenerateView.as_view(), name="sdk-generate"),
    path("metrics/", ApiMetricsView.as_view(), name="api-metrics"),
    *fhir_urlpatterns,
]
