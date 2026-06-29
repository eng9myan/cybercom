from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.deployment_profiles.views import (
    DeploymentCapabilityViewSet,
    DeploymentConfigurationViewSet,
    DeploymentProfileViewSet,
)

router = DefaultRouter()
router.register("profiles", DeploymentProfileViewSet)
router.register("configurations", DeploymentConfigurationViewSet)
router.register("capabilities", DeploymentCapabilityViewSet)

urlpatterns = [path("", include(router.urls))]
