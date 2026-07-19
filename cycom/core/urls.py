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
    path("api/v1/events/", include("platform.events.urls")),
    path("api/v1/common/", include("platform.common.urls")),
    path("api/v1/audit/", include("platform.audit.urls")),
    path("api/v1/ai/", include("platform.cyai.urls")),
    # ── Cycom accounting API v1 (Step 1) ────────────────────────────────────
    path("api/v1/accounting/", include("products.cycom.accounting.urls")),
    # ── Cycom AR/AP + invoicing API v1 (Step 2) ─────────────────────────────
    path("api/v1/ar-ap/", include("products.cycom.ar_ap.urls")),
    # ── Cycom HR + payroll API v1 (Step 3) ──────────────────────────────────
    path("api/v1/hr/", include("products.cycom.hr.urls")),
    path("api/v1/payroll/", include("products.cycom.payroll.urls")),
    # ── Cycom inventory API v1 (Step 4) ─────────────────────────────────────
    path("api/v1/inventory/", include("products.cycom.inventory.urls")),
    # ── Cycom per-user warehouse/product access control (Step 7) ────────────
    path("api/v1/access/", include("products.cycom.access.urls")),
    # ── Cycom POS API v1 (Step 5 — checkout/sessions/pricing core only) ────
    path("api/v1/pos/", include("products.cycom.pos.urls")),
    # ── Cycom CRM + procurement API v1 (Step 6) ─────────────────────────────
    path("api/v1/crm/", include("products.cycom.crm.urls")),
    path("api/v1/procurement/", include("products.cycom.procurement.urls")),
    # ── CyAI Local Memory Agent ──────────────────────────────────────────────
    path("api/v1/cyai-memory/", include("products.cycom.cyai_memory.urls")),
    path("api/v1/cyai-reports/", include("products.cycom.cyai_reports.urls")),
    path("api/v1/cyai-moduledev/", include("products.cycom.cyai_moduledev.urls")),
    path("api/v1/cyai-analytics/", include("products.cycom.cyai_analytics.urls")),
    # ── CyCom three-agent AI platform: registry/entitlement foundation ──────
    path("api/v1/cyai-platform/", include("products.cycom.cyai_platform.urls")),
    # ── Documents ─────────────────────────────────────────────────────────
    path("api/v1/documents/", include("products.cycom.documents.urls")),
    path("api/v1/expenses/", include("products.cycom.expenses.urls")),
    path("api/v1/calendar/", include("products.cycom.scheduler.urls")),
    path("api/v1/notes/", include("products.cycom.notes.urls")),
    path("api/v1/todo/", include("products.cycom.todo.urls")),
    path("api/v1/knowledge/", include("products.cycom.knowledge.urls")),
    path("api/v1/manufacturing/", include("products.cycom.manufacturing.urls")),
    path("api/v1/maintenance/", include("products.cycom.maintenance.urls")),
    path("api/v1/quality/", include("products.cycom.quality.urls")),
    path("api/v1/field-service/", include("products.cycom.field_service.urls")),
    path("api/v1/subscriptions/", include("products.cycom.subscriptions.urls")),
    path("api/v1/equity/", include("products.cycom.equity.urls")),
    path("api/v1/esg/", include("products.cycom.esg.urls")),
]
