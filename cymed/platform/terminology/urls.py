from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platform.terminology.views import TerminologyAuditLogViewSet, TerminologyViewSet

router = DefaultRouter()
router.register(r"logs", TerminologyAuditLogViewSet, basename="terminology-audit-log")
router.register(r"", TerminologyViewSet, basename="terminology")

urlpatterns = [
    path("", include(router.urls)),
]
