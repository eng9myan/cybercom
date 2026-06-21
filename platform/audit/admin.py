from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "action", "resource_type", "user_id", "tenant_id", "status", "ip_address"]
    list_filter = ["action", "status", "resource_type"]
    search_fields = ["user_id", "resource_id", "trace_id"]
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
