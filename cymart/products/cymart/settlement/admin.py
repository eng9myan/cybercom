from django.contrib import admin

from .models import SettlementLedgerEntry


@admin.register(SettlementLedgerEntry)
class SettlementLedgerEntryAdmin(admin.ModelAdmin):
    list_display = [
        "order_id", "tenant_id", "net_merchant_settlement", "cybercom_net_revenue",
        "is_refund_adjustment", "created_at",
    ]
    list_filter = ["is_refund_adjustment"]
    readonly_fields = [f.name for f in SettlementLedgerEntry._meta.fields]

    def has_delete_permission(self, request, obj=None):
        return False  # immutable ledger
