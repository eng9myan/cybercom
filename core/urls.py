from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.views.health import LivenessView, ReadinessView, HealthView

urlpatterns = [
    # ── Admin ──────────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Health / Observability ─────────────────────────────────────────────
    path("health", HealthView.as_view(), name="health-check"),
    path("health/liveness", LivenessView.as_view(), name="liveness-check"),
    path("health/readiness", ReadinessView.as_view(), name="readiness-check"),

    # ── OpenAPI Schema ─────────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # ── Platform API v1 ────────────────────────────────────────────────────
    path("api/v1/tenants/", include("platform.tenant.urls")),
    path("api/v1/identity/", include("platform.cyidentity.urls")),
    path("api/v1/events/", include("platform.events.urls")),
    path("api/v1/integration/", include("platform.cyintegrationhub.urls")),
    path("api/v1/data/", include("platform.cydata.urls")),
    path("api/v1/ai/", include("platform.cyai.urls")),
    path("api/v1/common/", include("platform.common.urls")),
    path("api/v1/terminology/", include("platform.terminology.urls")),
    
    # ── CyMed Clinical Core API v1 ──────────────────────────────────────────
    path("api/v1/patients/", include("products.cymed.core.patients.urls")),
    path("api/v1/providers/", include("products.cymed.core.providers.urls")),
    path("api/v1/organizations/", include("products.cymed.core.organizations.urls")),
    path("api/v1/facilities/", include("products.cymed.core.facilities.urls")),
    path("api/v1/encounters/", include("products.cymed.core.encounters.urls")),
    path("api/v1/clinical/", include("products.cymed.core.clinical.urls")),
    path("api/v1/documents/", include("products.cymed.core.documents.urls")),
    path("api/v1/careplans/", include("products.cymed.core.careplans.urls")),
    path("api/v1/orders/", include("products.cymed.core.orders.urls")),
    path("api/v1/scheduling/", include("products.cymed.core.scheduling.urls")),
    path("api/v1/consents/", include("products.cymed.core.consents.urls")),
    path("api/v1/registries/", include("products.cymed.core.registries.urls")),
    
    # ── CyMed Clinic Edition API v1 ──────────────────────────────────────────
    path("api/v1/clinic/", include("products.cymed.clinic.urls")),
]
