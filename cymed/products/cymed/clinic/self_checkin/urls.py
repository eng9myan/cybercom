from django.urls import path

from .views import KioskSessionViewSet


urlpatterns = [
    path("sessions/", KioskSessionViewSet.as_view({"get": "list"}), name="kiosk-list"),
    path("sessions/start/",
         KioskSessionViewSet.as_view({"post": "start_"}), name="kiosk-start"),
    path("sessions/<uuid:pk>/", KioskSessionViewSet.as_view({"get": "retrieve"}),
         name="kiosk-detail"),
    path("sessions/<uuid:pk>/identify/",
         KioskSessionViewSet.as_view({"post": "identify"}), name="kiosk-identify"),
    path("sessions/<uuid:pk>/verify-insurance/",
         KioskSessionViewSet.as_view({"post": "verify"}), name="kiosk-verify"),
    path("sessions/<uuid:pk>/sign-consent/",
         KioskSessionViewSet.as_view({"post": "consent"}), name="kiosk-consent"),
    path("sessions/<uuid:pk>/complete/",
         KioskSessionViewSet.as_view({"post": "complete_"}), name="kiosk-complete"),
]
