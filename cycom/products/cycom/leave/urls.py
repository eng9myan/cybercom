from rest_framework.routers import DefaultRouter

from products.cycom.leave.views import LeaveRequestViewSet, LeaveTypeViewSet

router = DefaultRouter()
router.register("types", LeaveTypeViewSet, basename="leave-type")
router.register("requests", LeaveRequestViewSet, basename="leave-request")

urlpatterns = router.urls
