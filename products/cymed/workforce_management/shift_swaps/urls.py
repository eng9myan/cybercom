from rest_framework.routers import DefaultRouter

from .views import ShiftSwapApprovalViewSet, ShiftSwapRequestViewSet, SwapValidationLogViewSet

router = DefaultRouter()
router.register("requests", ShiftSwapRequestViewSet, basename="shift-swap-request")
router.register("approvals", ShiftSwapApprovalViewSet, basename="shift-swap-approval")
router.register("validations", SwapValidationLogViewSet, basename="swap-validation-log")

urlpatterns = router.urls
