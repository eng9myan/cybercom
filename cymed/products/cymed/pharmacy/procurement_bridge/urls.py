"""Procurement Bridge URL routing."""

from rest_framework.routers import DefaultRouter

from .views import ProcurementRequestViewSet

router = DefaultRouter()
router.register(r"requests", ProcurementRequestViewSet, basename="procurement-request")

urlpatterns = router.urls
