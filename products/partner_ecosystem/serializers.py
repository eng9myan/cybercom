from rest_framework import serializers
from .models import (
    Partner, PartnerApplication, PartnerCertification, LeadRegistration,
    MarketplaceExtension, PartnerPortalAccess,
)


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PartnerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerApplication
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "submitted_at", "created_at", "updated_at"]


class PartnerCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCertification
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LeadRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadRegistration
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MarketplaceExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceExtension
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PartnerPortalAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerPortalAccess
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
