from django.urls import path, include
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.workspace.views import (
    ProviderWorkspaceViewSet,
    ProviderDashboardViewSet,
    ProviderPreferencesViewSet,
    WorkspaceSessionViewSet,
)

router = DefaultRouter()
router.register(r"workspaces", ProviderWorkspaceViewSet, basename="provider-workspace")
router.register(r"dashboards", ProviderDashboardViewSet, basename="provider-dashboard")
router.register(r"preferences", ProviderPreferencesViewSet, basename="provider-preferences")
router.register(r"sessions", WorkspaceSessionViewSet, basename="workspace-session")

urlpatterns = [
    path("", include(router.urls)),
]
