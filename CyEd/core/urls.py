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
    # ── CyEd group & campuses (multi-campus layer) ─────────────────────────
    path("api/v1/org/", include("products.cyed.org.urls")),
    # ── CyEd AU statutory compliance & reporting ───────────────────────────
    path("api/v1/compliance/", include("products.cyed.compliance.urls")),
    # ── CyEd Student Information System (Phase 0) ──────────────────────────
    path("api/v1/sis/", include("products.cyed.sis.urls")),
    # ── CyEd Gradebook (Phase 0) ───────────────────────────────────────────
    path("api/v1/gradebook/", include("products.cyed.gradebook.urls")),
    # ── CyEd AI agents registry (Phase 0 — curriculum tutor stub) ──────────
    path("api/v1/ai/", include("products.cyed.ai_agents.urls")),
    # ── CyEd academic layer (Phase 1-2) ────────────────────────────────────
    path("api/v1/curriculum/", include("products.cyed.curriculum.urls")),
    path("api/v1/timetable/", include("products.cyed.timetable.urls")),
    path("api/v1/attendance/", include("products.cyed.attendance.urls")),
    path("api/v1/reporting/", include("products.cyed.reporting.urls")),
    # ── CyEd engagement + operations (Phase 3) ─────────────────────────────
    path("api/v1/admissions/", include("products.cyed.admissions.urls")),
    path("api/v1/lms/", include("products.cyed.lms.urls")),
    path("api/v1/assessment/", include("products.cyed.assessment.urls")),
    # Security (MFA/step-up), payments, and SIF AU interoperability.
    path("api/v1/security/", include("products.cyed.security.urls")),
    path("api/v1/payments/", include("products.cyed.payments.urls")),
    # Gateway callbacks: no bearer token, no tenant header — HMAC-authenticated
    # over the raw body instead. Both auth and tenant middleware let
    # /api/v1/public/ through, so the webhook must live here.
    path("api/v1/public/payments/", include("products.cyed.payments.public_urls")),
    path("api/v1/sif/", include("products.cyed.sif.urls")),
    path("api/v1/wellbeing/", include("products.cyed.wellbeing.urls")),
    path("api/v1/fees/", include("products.cyed.fees.urls")),
    path("api/v1/analytics/", include("products.cyed.analytics.urls")),
    # ── Governance: RBAC-guarded audit trail + consent (Phase 6 remediation) ─
    path("api/v1/governance/", include("products.cyed.governance.urls")),
    path("api/v1/notifications/", include("products.cyed.notifications.urls")),
    path("api/v1/messaging/", include("products.cyed.messaging.urls")),
    path("api/v1/exams/", include("products.cyed.exams.urls")),
    path("api/v1/school/", include("products.cyed.school.urls")),
    path("api/v1/transport/", include("products.cyed.transport.urls")),
    path("api/v1/billing/", include("products.cyed.billing.urls")),
    path("api/v1/substitution/", include("products.cyed.substitution.urls")),
    path("api/v1/intake/", include("products.cyed.intake.urls")),
    path("api/v1/meetings/", include("products.cyed.meetings.urls")),
    path("api/v1/library/", include("products.cyed.library.urls")),
    path("api/v1/health/", include("products.cyed.health.urls")),
    path("api/v1/events/", include("products.cyed.events.urls")),
    path("api/v1/visitors/", include("products.cyed.visitors.urls")),
    # Native standalone ERP (CyED runs the back office itself).
    path("api/v1/staff-attendance/", include("products.cyed.staff_attendance.urls")),
    path("api/v1/docsign/", include("products.cyed.docsign.urls")),
    path("api/v1/hr/", include("products.cyed.hr.urls")),
    path("api/v1/payroll/", include("products.cyed.payroll.urls")),
    path("api/v1/finance/", include("products.cyed.finance.urls")),
    path("api/v1/procurement/", include("products.cyed.procurement.urls")),
    path("api/v1/inventory/", include("products.cyed.inventory.urls")),
    path("api/v1/assets/", include("products.cyed.assets.urls")),
    # Optional: also reuse CyCom's ERP over the API if CYED_CYCOM_URL is set.
    path("api/v1/erp/", include("products.cyed.erp.urls")),
]
