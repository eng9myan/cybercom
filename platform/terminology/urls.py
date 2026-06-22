from django.urls import path, include
from rest_framework.routers import DefaultRouter
from platform.terminology.views import TerminologyViewSet, TerminologyAuditLogViewSet

router = DefaultRouter()
router.register(r"logs", TerminologyAuditLogViewSet, basename="terminology-audit-log")
router.register(r"", TerminologyViewSet, basename="terminology")

urlpatterns = [
    path("", include(router.urls)),
]
