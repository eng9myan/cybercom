from rest_framework import serializers
from .models import (
    PricingPlan, Quotation, Proposal, LicenseKey,
    ComplianceCertification, CompetitiveBenchmark,
    License, Subscription, ProductEdition, FeatureFlag,
    TenantFeatureFlagOverride, WhiteLabelConfig, ConcurrentLicenseSession,
    CustomerPortalAccess, SupportTicket, MarketplaceListing,
    MarketplaceInstallation, CommercialMetricsSnapshot,
)


class PricingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingPlan
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LicenseKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseKey
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "issued_at", "created_at", "updated_at"]


class ComplianceCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceCertification
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CompetitiveBenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitiveBenchmark
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProductEditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductEdition
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantFeatureFlagOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantFeatureFlagOverride
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "overridden_at", "created_at", "updated_at"]


class WhiteLabelConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteLabelConfig
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ConcurrentLicenseSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConcurrentLicenseSession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "started_at", "last_heartbeat_at", "created_at", "updated_at"]


class CustomerPortalAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPortalAccess
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "ticket_number", "submitted_by_id", "created_at", "updated_at"]


class MarketplaceListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceListing
        fields = "__all__"
        read_only_fields = ["id", "install_count", "rating_avg", "rating_count", "created_at", "updated_at"]


class MarketplaceInstallationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceInstallation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "installed_at", "created_at", "updated_at"]


class CommercialMetricsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommercialMetricsSnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
