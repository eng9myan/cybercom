from django.contrib import admin

from .models import MarketplaceOrder, MarketplaceOrderLine, OrderStatusHistory


class MarketplaceOrderLineInline(admin.TabularInline):
    model = MarketplaceOrderLine
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "reason", "actor_id", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MarketplaceOrder)
class MarketplaceOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant_id", "status", "total_amount", "created_at"]
    list_filter = ["status", "fulfillment_type"]
    search_fields = ["idempotency_key", "id"]
    inlines = [MarketplaceOrderLineInline, OrderStatusHistoryInline]
