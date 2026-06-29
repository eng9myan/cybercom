from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tier", "status", "country_code", "activated_at", "created_at"]
    list_filter = ["status", "tier", "country_code"]
    search_fields = ["name", "slug", "domain"]
    readonly_fields = ["id", "created_at", "updated_at", "activated_at", "suspended_at"]
    ordering = ["name"]
