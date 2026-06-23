"""Procurement Bridge URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcurementRequestViewSet

router = DefaultRouter()
router.register(r"requests", ProcurementRequestViewSet, basename="procurement-request")

urlpatterns = router.urls
