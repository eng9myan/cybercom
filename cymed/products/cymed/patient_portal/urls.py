from django.urls import path

from .views import (
    ConsentGrantViewSet,
    DelegatedAccessViewSet,
    EmergencyProfileView,
    NFCCardViewSet,
    NFCChallengeView,
    NFCScanLogViewSet,
    NFCScanView,
    PatientDeviceViewSet,
    PatientPortalActivityViewSet,
    PatientPortalNotificationPreferenceViewSet,
    PatientPortalProfileViewSet,
)

# Standard CRUD helpers (avoid DefaultRouter to keep URL layout explicit)
def _viewset(vs, actions):
    return vs.as_view(actions)


urlpatterns = [
    # Profile
    path("profiles/", _viewset(PatientPortalProfileViewSet, {"get": "list", "post": "create"}),
         name="patient-portal-profile-list"),
    path("profiles/<uuid:pk>/", _viewset(PatientPortalProfileViewSet,
                                          {"get": "retrieve", "put": "update",
                                           "patch": "partial_update", "delete": "destroy"}),
         name="patient-portal-profile-detail"),
    path("profiles/<uuid:pk>/activities/",
         _viewset(PatientPortalProfileViewSet, {"get": "activities"}),
         name="patient-portal-activities"),
    path("profiles/<uuid:pk>/notification-preferences/",
         _viewset(PatientPortalProfileViewSet, {"get": "notification_preferences"}),
         name="patient-portal-notifications"),

    # Devices
    path("devices/", _viewset(PatientDeviceViewSet, {"get": "list", "post": "create"}),
         name="patient-device-list"),
    path("devices/<uuid:pk>/", _viewset(PatientDeviceViewSet,
                                         {"get": "retrieve", "delete": "destroy"}),
         name="patient-device-detail"),
    path("devices/<uuid:pk>/revoke/",
         _viewset(PatientDeviceViewSet, {"post": "revoke"}),
         name="patient-device-revoke"),

    # NFC (patient / staff)
    path("nfc/cards/", _viewset(NFCCardViewSet, {"get": "list", "post": "create"}),
         name="nfc-card-list"),
    path("nfc/cards/<uuid:pk>/", _viewset(NFCCardViewSet, {"get": "retrieve"}),
         name="nfc-card-detail"),
    path("nfc/cards/<uuid:pk>/activate/",
         _viewset(NFCCardViewSet, {"post": "activate"}),
         name="nfc-card-activate"),
    path("nfc/cards/<uuid:pk>/revoke/",
         _viewset(NFCCardViewSet, {"post": "revoke"}),
         name="nfc-card-revoke"),
    path("nfc/scans/", _viewset(NFCScanLogViewSet, {"get": "list"}),
         name="nfc-scan-list"),

    # NFC public (provider terminals)
    path("nfc/challenge/", NFCChallengeView.as_view(), name="nfc-challenge"),
    path("nfc/scan/",      NFCScanView.as_view(),      name="nfc-scan"),

    # Emergency
    path("emergency/", EmergencyProfileView.as_view(), name="emergency-profile"),

    # Delegation
    path("delegations/", _viewset(DelegatedAccessViewSet, {"get": "list", "post": "create"}),
         name="delegation-list"),
    path("delegations/<uuid:pk>/", _viewset(DelegatedAccessViewSet,
                                             {"get": "retrieve", "delete": "destroy"}),
         name="delegation-detail"),
    path("delegations/<uuid:pk>/accept/",
         _viewset(DelegatedAccessViewSet, {"post": "accept"}),
         name="delegation-accept"),
    path("delegations/<uuid:pk>/revoke/",
         _viewset(DelegatedAccessViewSet, {"post": "revoke"}),
         name="delegation-revoke"),

    # Consent
    path("consents/", _viewset(ConsentGrantViewSet, {"get": "list", "post": "create"}),
         name="consent-list"),
    path("consents/<uuid:pk>/",
         _viewset(ConsentGrantViewSet, {"get": "retrieve", "delete": "destroy"}),
         name="consent-detail"),

    # Notification prefs (kept from prior version)
    path("notification-preferences/",
         _viewset(PatientPortalNotificationPreferenceViewSet, {"get": "list", "post": "create"}),
         name="patient-portal-pref-list"),
    path("notification-preferences/<uuid:pk>/",
         _viewset(PatientPortalNotificationPreferenceViewSet,
                  {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
         name="patient-portal-pref-detail"),

    # Legacy activity list
    path("activities/", _viewset(PatientPortalActivityViewSet, {"get": "list"}),
         name="patient-portal-activity-list"),
]
