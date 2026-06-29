from products.cymed.commercial.deployment_profiles.models import (
    DeploymentCapability,
    DeploymentConfiguration,
    DeploymentProfile,
)
from products.cymed.commercial.deployment_profiles.serializers import (
    DeploymentCapabilitySerializer,
    DeploymentConfigurationSerializer,
    DeploymentProfileSerializer,
)
from products.cymed.commercial.views import CommercialModelViewSet


class DeploymentProfileViewSet(CommercialModelViewSet):
    queryset = DeploymentProfile.objects.all()
    serializer_class = DeploymentProfileSerializer


class DeploymentConfigurationViewSet(CommercialModelViewSet):
    queryset = DeploymentConfiguration.objects.all()
    serializer_class = DeploymentConfigurationSerializer


class DeploymentCapabilityViewSet(CommercialModelViewSet):
    queryset = DeploymentCapability.objects.all()
    serializer_class = DeploymentCapabilitySerializer
