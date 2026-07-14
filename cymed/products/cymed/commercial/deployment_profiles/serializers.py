from rest_framework import serializers

from products.cymed.commercial.deployment_profiles.models import (
    DeploymentCapability,
    DeploymentConfiguration,
    DeploymentProfile,
)


class DeploymentCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeploymentCapability
        fields = "__all__"


class DeploymentProfileSerializer(serializers.ModelSerializer):
    capabilities = DeploymentCapabilitySerializer(many=True, read_only=True)

    class Meta:
        model = DeploymentProfile
        fields = "__all__"


class DeploymentConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeploymentConfiguration
        fields = "__all__"
