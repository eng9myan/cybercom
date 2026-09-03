from rest_framework import serializers

from platform.provisioning.models import (
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
            "companies", "branches", "warehouses", "factories", "projects",
            "departments", "cost_centers", "status", "template_version_used",
            "summary", "provisioned_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "tenant_id", "status", "template_version_used", "summary",
            "provisioned_at", "created_at", "updated_at",
        ]
