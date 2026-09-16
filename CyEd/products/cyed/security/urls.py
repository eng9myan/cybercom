from django.urls import path
from rest_framework.routers import DefaultRouter

from products.cyed.security.views import (
    LoginAttemptViewSet,
    MfaBackupCodesView,
    MfaConfirmView,
    MfaDisableView,
    MfaEnrollView,
    MfaEnrollmentViewSet,
    MfaStatusView,
    MfaVerifyView,
    SecurityEventViewSet,
)

router = DefaultRouter()
router.register("enrollments", MfaEnrollmentViewSet, basename="mfa-enrollment")
router.register("events", SecurityEventViewSet, basename="security-event")
router.register("login-attempts", LoginAttemptViewSet, basename="login-attempt")

urlpatterns = [
    path("mfa/status/", MfaStatusView.as_view(), name="mfa-status"),
    path("mfa/enroll/", MfaEnrollView.as_view(), name="mfa-enroll"),
    path("mfa/confirm/", MfaConfirmView.as_view(), name="mfa-confirm"),
    path("mfa/verify/", MfaVerifyView.as_view(), name="mfa-verify"),
    path("mfa/disable/", MfaDisableView.as_view(), name="mfa-disable"),
    path("mfa/backup-codes/", MfaBackupCodesView.as_view(), name="mfa-backup-codes"),
]
urlpatterns += router.urls
