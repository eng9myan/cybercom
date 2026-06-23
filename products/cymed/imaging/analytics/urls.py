from rest_framework.routers import DefaultRouter
from .views import (
    ImagingOperationsDashboardViewSet, RadiologistProductivityViewSet,
    TeleradiologyDashboardViewSet, ImagingRevenueEventViewSet,
)

router = DefaultRouter()
router.register("ops-dashboard", ImagingOperationsDashboardViewSet, basename="imaging-ops-dashboard")
router.register("radiologist-productivity", RadiologistProductivityViewSet, basename="radiologist-productivity")
router.register("teleradiology-dashboard", TeleradiologyDashboardViewSet, basename="teleradiology-dashboard")
router.register("revenue-events", ImagingRevenueEventViewSet, basename="imaging-revenue-event")

urlpatterns = router.urls
