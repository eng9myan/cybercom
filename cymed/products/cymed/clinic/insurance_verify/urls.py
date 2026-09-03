from django.urls import path

from .views import VerifyAtCheckinView, VerifyBeforeAppointmentView


urlpatterns = [
    path("verify/before-appointment/", VerifyBeforeAppointmentView.as_view(),
         name="clinic-verify-before"),
    path("verify/at-checkin/", VerifyAtCheckinView.as_view(),
         name="clinic-verify-checkin"),
]
