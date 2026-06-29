"""
Audit & Compliance API URL routing.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditArchiveViewSet,
    AuditCategoryViewSet,
    AuditChainViewSet,
    AuditEntryViewSet,
    AuditEventViewSet,
    AuditExportViewSet,
    AuditLogViewSet,
    AuditRetentionPolicyViewSet,
    AuditSignatureViewSet,
    ComplianceAssessmentViewSet,
    ComplianceProfileViewSet,
    ComplianceReportViewSet,
    ComplianceRuleViewSet,
    ComplianceViolationViewSet,
    EvidencePackageViewSet,
    EvidenceRecordViewSet,
    LegalHoldViewSet,
    audit_health,
    audit_metrics,
)

router = DefaultRouter()
router.register(r"logs", AuditLogViewSet, basename="audit-log")
router.register(r"events", AuditEventViewSet, basename="audit-event")
router.register(r"categories", AuditCategoryViewSet, basename="audit-category")
router.register(r"chains", AuditChainViewSet, basename="audit-chain")
router.register(r"entries", AuditEntryViewSet, basename="audit-entry")
router.register(r"retention-policies", AuditRetentionPolicyViewSet, basename="audit-retention")
router.register(r"archives", AuditArchiveViewSet, basename="audit-archive")
router.register(r"signatures", AuditSignatureViewSet, basename="audit-signature")
router.register(r"exports", AuditExportViewSet, basename="audit-export")
router.register(r"legal-holds", LegalHoldViewSet, basename="legal-hold")
router.register(r"compliance/profiles", ComplianceProfileViewSet, basename="compliance-profile")
router.register(r"compliance/rules", ComplianceRuleViewSet, basename="compliance-rule")
router.register(
    r"compliance/violations", ComplianceViolationViewSet, basename="compliance-violation"
)
router.register(
    r"compliance/assessments", ComplianceAssessmentViewSet, basename="compliance-assessment"
)
router.register(r"compliance/reports", ComplianceReportViewSet, basename="compliance-report")
router.register(r"evidence/records", EvidenceRecordViewSet, basename="evidence-record")
router.register(r"evidence/packages", EvidencePackageViewSet, basename="evidence-package")

urlpatterns = [
    path("healthz/", audit_health, name="audit-health"),
    path("metrics", audit_metrics, name="audit-metrics"),
    path("", include(router.urls)),
]
