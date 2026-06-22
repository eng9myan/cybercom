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
]
