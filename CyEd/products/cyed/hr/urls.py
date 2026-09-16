from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.hr.views import (
    ContractViewSet, LeaveEntitlementViewSet, OnboardingTaskViewSet, PerformanceReviewViewSet,
    StaffClearanceViewSet, StaffLeaveViewSet, StaffViewSet,
)

router = DefaultRouter()
router.register("staff", StaffViewSet)
router.register("contracts", ContractViewSet)
router.register("leave", StaffLeaveViewSet)
router.register("leave-entitlements", LeaveEntitlementViewSet)
router.register("clearances", StaffClearanceViewSet)
router.register("performance-reviews", PerformanceReviewViewSet)
router.register("onboarding-tasks", OnboardingTaskViewSet)

urlpatterns = [path("", include(router.urls))]
