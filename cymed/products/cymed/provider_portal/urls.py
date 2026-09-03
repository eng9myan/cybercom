from django.urls import path

from .views import (
    ProviderCredentialingStatusViewSet,
    ProviderPortalActivityViewSet,
    ProviderPortalProfileViewSet,
)

urlpatterns = [
    path("profiles/", ProviderPortalProfileViewSet.as_view({"get": "list", "post": "create"}), name="provider-portal-profile-list"),
    path("profiles/<str:pk>/", ProviderPortalProfileViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="provider-portal-profile-detail"),
    path("profiles/<str:pk>/toggle-on-call/", ProviderPortalProfileViewSet.as_view({"post": "toggle_on_call"}), name="provider-portal-oncall"),
    path("profiles/<str:pk>/activities/", ProviderPortalProfileViewSet.as_view({"get": "activities"}), name="provider-portal-activities"),
    path("activities/", ProviderPortalActivityViewSet.as_view({"get": "list"}), name="provider-portal-activity-list"),
    path("credentialing/", ProviderCredentialingStatusViewSet.as_view({"get": "list", "post": "create"}), name="provider-credentialing-list"),
    path("credentialing/<str:pk>/", ProviderCredentialingStatusViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="provider-credentialing-detail"),
    path("credentialing/<str:pk>/verify/", ProviderCredentialingStatusViewSet.as_view({"post": "verify"}), name="provider-credentialing-verify"),
]
