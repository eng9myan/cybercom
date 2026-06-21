from django.contrib import admin
from .models import IdentityRealm, ServicePrincipal


@admin.register(IdentityRealm)
class IdentityRealmAdmin(admin.ModelAdmin):
    list_display = ["realm_name", "tenant_id", "is_active", "mfa_enforced", "passkey_enabled"]
    list_filter = ["is_active", "mfa_enforced"]
    search_fields = ["realm_name", "client_id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ServicePrincipal)
class ServicePrincipalAdmin(admin.ModelAdmin):
    list_display = ["name", "realm", "client_id", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "client_id"]
    readonly_fields = ["id", "created_at", "updated_at"]
