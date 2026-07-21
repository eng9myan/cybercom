from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.views.health import HealthView, LivenessView, ReadinessView

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
    # ── Shared platform API v1 ──────────────────────────────────────────────
    path("api/v1/identity/", include("platform.cyidentity.urls")),
    # ── CyVault files API v1 ─────────────────────────────────────────────────
    path("api/v1/files/", include("products.cyvault.files.urls")),
]
