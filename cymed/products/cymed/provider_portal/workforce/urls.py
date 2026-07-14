from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.workforce.views import (
    AttendanceRecordViewSet,
    CredentialExpiryViewSet,
    LeaveRequestViewSet,
    ProviderScheduleViewSet,
    ShiftAssignmentViewSet,
)

router = DefaultRouter()
router.register(r"schedules", ProviderScheduleViewSet, basename="provider-schedule")
router.register(r"shift-assignments", ShiftAssignmentViewSet, basename="shift-assignment")
router.register(r"leave-requests", LeaveRequestViewSet, basename="leave-request")
router.register(r"attendance", AttendanceRecordViewSet, basename="attendance-record")
router.register(r"credential-expiry", CredentialExpiryViewSet, basename="credential-expiry")

urlpatterns = [
    path("", include(router.urls)),
]
