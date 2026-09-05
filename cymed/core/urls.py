from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.views.health import HealthView, LivenessView, ReadinessView
from core.views.portals import MainDashboardView, PatientPortalView, ProviderPortalView

urlpatterns = [
    # ── Admin ──────────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),
    # ── Health / Observability ─────────────────────────────────────────────
    path("health", HealthView.as_view(), name="health-check"),
    path("health/liveness", LivenessView.as_view(), name="liveness-check"),
    path("health/readiness", ReadinessView.as_view(), name="readiness-check"),
    path("", include("platform.observability.urls")),   # exposes /metrics
    # ── Frontend Portals ───────────────────────────────────────────────────
    path("", MainDashboardView.as_view(), name="home"),
    path("patient-portal/", PatientPortalView.as_view(), name="patient-portal"),
    path("patient-app/", TemplateView.as_view(template_name="patient_app/index.html"), name="patient-app"),
    path("provider-portal/", ProviderPortalView.as_view(), name="provider-portal"),
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
    path("api/v1/canonical/", include("platform.canonical.urls")),
    # Language switch for the server-rendered portals (POST target of the
    # header toggle in base.html). Django's built-in set_language view.
    path("i18n/", include("django.conf.urls.i18n")),
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
    # ── CyMed Integrations API v1 ──────────────────────────────────────────
    path("api/v1/integrations/jofawtra/", include("products.cymed.integrations.jofawtra.urls")),
    path("api/v1/integrations/zakata/", include("products.cymed.integrations.zakata.urls")),
    path("api/v1/integrations/nphies/", include("products.cymed.integrations.nphies.urls")),
    path("api/v1/integrations/hakeem/", include("products.cymed.integrations.hakeem.urls")),
    # ── FHIR R4 REST Server (P0-4) ─────────────────────────────────────────
    path("fhir/R4/", include("products.cymed.fhir_r4.urls")),
    # ── AI Clinical Decision Support (P0-5) ────────────────────────────────
    path("api/v1/ai-cds/", include("products.cymed.ai_cds.urls")),
    # ── Revenue Cycle Management (P0-6) ────────────────────────────────────
    path("api/v1/rcm/", include("products.cymed.rcm.urls")),
    # ── Clinic gap-fill (P0-8) ─────────────────────────────────────────────
    path("api/v1/clinic/insurance/",  include("products.cymed.clinic.insurance_verify.urls")),
    path("api/v1/clinic/kiosk/",      include("products.cymed.clinic.self_checkin.urls")),
    path("api/v1/clinic/coding/",     include("products.cymed.clinic.auto_coding.urls")),
    path("api/v1/clinic/referrals/",  include("products.cymed.clinic.referral_loop.urls")),
    path("api/v1/clinic/shop/",       include("products.cymed.clinic.ecommerce.urls")),
    path("api/v1/clinic/marketing/",  include("products.cymed.clinic.marketing.urls")),
    # ── CyMed Portals API v1 ───────────────────────────────────────────────
    path("api/v1/patient-portal/", include("products.cymed.patient_portal.urls")),
    # Alias per P0-1 spec: mobile app uses /patient-app/
    path("api/v1/patient-app/",    include("products.cymed.patient_portal.urls")),
    path("api/v1/provider-portal/", include("products.cymed.provider_portal.urls")),
    # ── CyMed Ecosystem Glue (P0-12) ───────────────────────────────────────
    path("api/v1/ecosystem/",        include("products.cymed.ecosystem.urls")),
    # ── CyMed MRFF Program (MRFF-16..19) ───────────────────────────────────
    path("api/v1/mrff/",             include("products.cymed.mrff.urls")),
    # ── Payments (P0-2) ────────────────────────────────────────────────────
    path("api/v1/payments/",         include("products.cymed.payments.urls")),
    path("api/v1/patient-app/billing/", include("products.cymed.payments.urls")),
]
