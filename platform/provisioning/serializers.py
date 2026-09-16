from rest_framework import serializers

from platform.provisioning.models import (
    ApprovalPolicy,
    ApprovalTier,
    CompanyBlueprint,
    CountryPack,
    DepartmentPack,
    IndustryTemplate,
    TenantConfigParameter,
)


class TenantConfigParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantConfigParameter
        fields = ["id", "key", "value", "updated_at"]
        read_only_fields = ["id", "tenant_id", "updated_at"]


class CountryPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryPack
        fields = [
            "code", "name", "currency", "languages", "default_locale",
            "fiscal_year_start_month", "tax_config", "payroll_config",
            "einvoicing", "public_holidays", "version",
        ]


class DepartmentPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentPack
        fields = [
            "key", "name", "description", "modules", "roles", "kpis",
            "dashboards", "reports", "version",
        ]


class IndustryTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryTemplate
        fields = [
            "key", "name", "description", "department_pack_keys", "terminology",
            "approval_matrix", "categories", "dashboards", "reports",
            "doc_templates", "import_templates", "industry_fields",
            "recommended_ops", "version",
        ]


class CompanyBlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyBlueprint
        fields = [
            "id", "company_name", "country_code", "industry_key", "size",
            "setup_level", "business_ops", "selected_department_packs",
            "approval_overrides",
            "companies", "branches", "warehouses", "factories", "projects",
            "departments", "cost_centers", "status", "template_version_used",
            "summary", "provisioned_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "tenant_id", "status", "template_version_used", "summary",
            "provisioned_at", "created_at", "updated_at",
        ]


class ApprovalTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalTier
        fields = ["id", "sequence", "threshold_min", "threshold_max", "approver_role"]
        read_only_fields = ["id"]


class ApprovalPolicySerializer(serializers.ModelSerializer):
    """Post-setup editing of a provisioned approval chain. `tiers` is a full
    replace on write (same semantics as ProvisioningService._generate_approvals)
    so callers always PATCH the whole ladder rather than patching one band."""

    tiers = ApprovalTierSerializer(many=True)

    class Meta:
        model = ApprovalPolicy
        fields = ["id", "document_type", "name", "currency", "is_active", "tiers"]
        read_only_fields = ["id", "document_type", "currency"]

    def validate_tiers(self, tiers):
        if not tiers:
            return tiers
        ordered = sorted(tiers, key=lambda t: t.get("sequence") or 0)
        for i, tier in enumerate(ordered):
            tmax = tier.get("threshold_max")
            if tmax is not None and tmax <= tier.get("threshold_min", 0):
                raise serializers.ValidationError(
                    "Each tier's max must be greater than its min."
                )
            if i < len(ordered) - 1 and tmax is None:
                raise serializers.ValidationError(
                    "Only the last tier may be open-ended (no max)."
                )
        return tiers

    def update(self, instance, validated_data):
        tiers = validated_data.pop("tiers", None)
        instance = super().update(instance, validated_data)
        if tiers is not None:
            instance.tiers.all().delete()
            for i, tier in enumerate(tiers, start=1):
                ApprovalTier.objects.create(
                    tenant_id=instance.tenant_id,
                    policy=instance,
                    sequence=tier.get("sequence") or i,
                    threshold_min=tier.get("threshold_min", 0),
                    threshold_max=tier.get("threshold_max"),
                    approver_role=tier["approver_role"],
                )
        return instance
