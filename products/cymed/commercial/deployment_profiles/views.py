from products.cymed.commercial.views import CommercialModelViewSet
from products.cymed.commercial.deployment_profiles.models import (
    DeploymentProfile, DeploymentConfiguration, DeploymentCapability
)
from products.cymed.commercial.deployment_profiles.serializers import (
    DeploymentProfileSerializer, DeploymentConfigurationSerializer, DeploymentCapabilitySerializer
)


class DeploymentProfileViewSet(CommercialModelViewSet):
    queryset = DeploymentProfile.objects.all()
    serializer_class = DeploymentProfileSerializer


class DeploymentConfigurationViewSet(CommercialModelViewSet):
    queryset = DeploymentConfiguration.objects.all()
    serializer_class = DeploymentConfigurationSerializer


class DeploymentCapabilityViewSet(CommercialModelViewSet):
    queryset = DeploymentCapability.objects.all()
    serializer_class = DeploymentCapabilitySerializer
