from rest_framework import serializers
from products.cymed.commercial.feature_flags.models import (
    FeatureFlag, FeatureDependency, TenantFeature, CustomerFeature
)


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = "__all__"


class FeatureDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureDependency
        fields = "__all__"


class TenantFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantFeature
        fields = "__all__"


class CustomerFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeature
        fields = "__all__"


class FeatureCheckSerializer(serializers.Serializer):
    """Check if a feature is enabled for the current tenant."""
    feature_code = serializers.CharField()
