from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChargeViewSet,
    ChargeItemViewSet,
    ChargeRuleViewSet,
    ChargeAdjustmentViewSet,
    ChargeAuditViewSet,
)

router = DefaultRouter()
router.register(r"charges", ChargeViewSet, basename="charge")
router.register(r"charge-items", ChargeItemViewSet, basename="charge-item")
router.register(r"charge-rules", ChargeRuleViewSet, basename="charge-rule")
router.register(r"adjustments", ChargeAdjustmentViewSet, basename="charge-adjustment")
router.register(r"audits", ChargeAuditViewSet, basename="charge-audit")

urlpatterns = [
    path("", include(router.urls)),
]
