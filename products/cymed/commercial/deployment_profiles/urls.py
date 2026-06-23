from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.deployment_profiles.views import (
    DeploymentProfileViewSet, DeploymentConfigurationViewSet, DeploymentCapabilityViewSet
)

router = DefaultRouter()
router.register("profiles", DeploymentProfileViewSet)
router.register("configurations", DeploymentConfigurationViewSet)
router.register("capabilities", DeploymentCapabilityViewSet)

urlpatterns = [path("", include(router.urls))]
