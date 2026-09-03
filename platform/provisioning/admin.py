from django.contrib import admin

from platform.provisioning.models import (
    ApprovalPolicy,
    ApprovalTier,
    CompanyBlueprint,
    CountryPack,
    DepartmentPack,
    IndustryTemplate,
)


@admin.register(CountryPack)
class CountryPackAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "currency", "version", "is_active")


@admin.register(DepartmentPack)
class DepartmentPackAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "version", "is_active")


@admin.register(IndustryTemplate)
class IndustryTemplateAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "version", "is_active")


@admin.register(CompanyBlueprint)
class CompanyBlueprintAdmin(admin.ModelAdmin):
    list_display = ("company_name", "industry_key", "size", "status", "provisioned_at")
    list_filter = ("status", "industry_key", "size")


class ApprovalTierInline(admin.TabularInline):
    model = ApprovalTier
    extra = 0


@admin.register(ApprovalPolicy)
class ApprovalPolicyAdmin(admin.ModelAdmin):
    list_display = ("document_type", "name", "currency", "is_active")
    inlines = [ApprovalTierInline]
