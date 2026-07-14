from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegisterView, UserLoginView, UserLogoutView, PasswordResetView,
    MfaToggleView, GoogleOAuthView, MicrosoftOAuthView, UserViewSet,
    RoleViewSet, PermissionViewSet, PermissionGroupViewSet,
    RoleAssignmentViewSet, UserProfileViewSet, UserSessionViewSet, UserDeviceViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'permission-groups', PermissionGroupViewSet, basename='permission-group')
router.register(r'role-assignments', RoleAssignmentViewSet, basename='role-assignment')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'sessions', UserSessionViewSet, basename='session')
router.register(r'devices', UserDeviceViewSet, basename='device')

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('mfa/', MfaToggleView.as_view(), name='mfa-toggle'),
    path('google-login/', GoogleOAuthView.as_view(), name='google-login'),
    path('microsoft-login/', MicrosoftOAuthView.as_view(), name='microsoft-login'),
    path('', include(router.urls)),
]
