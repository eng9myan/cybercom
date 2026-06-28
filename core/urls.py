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
    path("api/v1/notifications/", include("platform.notifications.urls")),
    path("api/v1/audit/", include("platform.audit.urls")),

    # ── CyCom ERP API v1 ───────────────────────────────────────────────────
    path("api/v1/erp/", include("products.cycom.urls")),

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

    # ── CyMed Patient Portal API v1 (Program 3.6) ─────────────────────────
    path("api/v1/patient-portal/", include("products.cymed.patient_portal.urls")),

    # ── CyMed Provider Portal API v1 (Program 3.7) ────────────────────────
    path("api/v1/provider-portal/", include("products.cymed.provider_portal.urls")),

    # ── CyMed RCM & Insurance Platform API v1 (Program 3.8) ───────────────
    path("api/v1/rcm/", include("products.cymed.rcm.urls")),

    # ── CyMed Population Health API v1 (Program 3.9) ──────────────────────
    path("api/v1/population-health/", include("products.cymed.population_health.urls")),

    # ── CyMed Workforce Management API v1 (Program 3.10) ──────────────────
    path("api/v1/workforce/", include("products.cymed.workforce_management.urls")),

    # ── CyberCom Sales Demo Platform API v1 (Program 3.11) ────────────────
    path("api/v1/demo/", include("products.demo.urls")),

    # ── CyberCom Deployment Platform API v1 (Program 3.12) ────────────────
    path("api/v1/deployment/", include("products.deployment.urls")),

    # ── CyberCom Implementation Methodology API v1 (Program 3.13) ─────────
    path("api/v1/implementation/", include("products.implementation.urls")),

    # ── CyberCom Academy API v1 (Program 3.14) ────────────────────────────
    path("api/v1/academy/", include("products.academy.urls")),

    # ── CyberCom Commercial Readiness API v1 (Program 3.15) ───────────────
    path("api/v1/commercial-readiness/", include("products.commercial_readiness.urls")),

    # ── CyberCom Partner Ecosystem API v1 (Program 3.16) ──────────────────
    path("api/v1/partners/", include("products.partner_ecosystem.urls")),

    # ── Website Public APIs & CMS ──────────────────────────────────────────
    path("api/v1/public/", include("products.website.urls", namespace="website")),
]
