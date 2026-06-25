from rest_framework import serializers
from .models import (
    PricingPlan, Quotation, Proposal, LicenseKey,
    ComplianceCertification, CompetitiveBenchmark,
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
