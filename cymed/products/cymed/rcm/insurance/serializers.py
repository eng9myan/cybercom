from rest_framework import serializers

from .models import (
    Benefit,
    Coverage,
    CoverageRule,
    InsuranceCard,
    InsuranceCompany,
    InsuranceMember,
    InsurancePlan,
)


class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCompany
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class InsurancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePlan
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class InsurancePlanNestedSerializer(serializers.ModelSerializer):
    """Lightweight nested representation of InsurancePlan."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = InsurancePlan
        fields = ["id", "plan_name", "plan_code", "plan_type", "company_name"]
        read_only_fields = fields


class InsuranceMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceMember
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coverage
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class BenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefit
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CoverageRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverageRule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class InsuranceCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCard
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
