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
    # ── Platform API v1 ────────────────────────────────────────────────────
    path("api/v1/public/", include("platform.tenant.urls_public")),
    path("api/v1/tenants/", include("platform.tenant.urls")),
    path("api/v1/identity/", include("platform.cyidentity.urls")),
    path("api/v1/wallet/", include("platform.wallet.urls")),
    path("api/v1/events/", include("platform.events.urls")),
    path("api/v1/integration/", include("platform.cyintegrationhub.urls")),
    path("api/v1/data/", include("platform.cydata.urls")),
    path("api/v1/ai/", include("platform.cyai.urls")),
    path("api/v1/common/", include("platform.common.urls")),
    path("api/v1/terminology/", include("platform.terminology.urls")),
    path("api/v1/notifications/", include("platform.notifications.urls")),
    path("api/v1/audit/", include("platform.audit.urls")),
    # ── CyMed Clinical Core API v1 (Program 3.0) ───────────────────────────
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
    path("api/v1/commerce/", include("products.cymed.core.commerce.urls")),
    # ── CyMed Commercial Foundation API v1 (Program 3.C0) ─────────────────
    path("api/v1/commercial/", include("products.cymed.commercial.urls")),
    # ── CyMed Clinic Edition API v1 (Program 3.1) ─────────────────────────
    path("api/v1/clinic/", include("products.cymed.clinic.urls")),
    # ── CyMed Hospital Edition API v1 (Program 3.2) ───────────────────────
    path("api/v1/hospital/", include("products.cymed.hospital.urls")),
    # ── CyMed Laboratory Edition API v1 (Program 3.3) ─────────────────────
    path("api/v1/lab/", include("products.cymed.laboratory.urls")),
    # ── CyMed Imaging Edition API v1 (Program 3.4) ────────────────────────
    path("api/v1/imaging/", include("products.cymed.imaging.urls")),
    # ── CyMed Pharmacy Edition API v1 (Program 3.5) ───────────────────────
    path("api/v1/pharmacy/", include("products.cymed.pharmacy.urls")),
    # NOTE: patient_portal, provider_portal, rcm, population_health,
    # workforce_management, demo, deployment, implementation, academy,
    # commercial_readiness, partner_ecosystem, and website routes were
    # removed along with their app directories — out of scope for this
    # monorepo's CyMed clinical subset (see cymed/README or repo root docs).
]
