from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.PatientPortalAccountViewSet, basename='portal-account')
router.register(r'profiles', views.PatientProfileViewSet, basename='portal-profile')
router.register(r'preferences', views.PatientPreferencesViewSet, basename='portal-preferences')
router.register(r'security-settings', views.PatientSecuritySettingsViewSet, basename='portal-security-settings')
router.register(r'devices', views.PatientDeviceViewSet, basename='portal-device')

urlpatterns = [path('', include(router.urls))]
