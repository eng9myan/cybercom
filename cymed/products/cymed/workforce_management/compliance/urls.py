from rest_framework.routers import DefaultRouter

from .views import (
    ComplianceAuditLogViewSet,
    RamadanComplianceRuleViewSet,
    WardRatioConfigViewSet,
    WorkforceComplianceConfigViewSet,
)

router = DefaultRouter()
router.register("configs", WorkforceComplianceConfigViewSet, basename="compliance-config")
router.register("ramadan-rules", RamadanComplianceRuleViewSet, basename="ramadan-rule")
router.register("ward-ratios", WardRatioConfigViewSet, basename="ward-ratio-config")
router.register("audit-logs", ComplianceAuditLogViewSet, basename="compliance-audit-log")

urlpatterns = router.urls
