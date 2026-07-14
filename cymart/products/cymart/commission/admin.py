from django.contrib import admin

from .models import CommissionCalculation, CommissionPolicy, CommissionTier


class CommissionTierInline(admin.TabularInline):
    model = CommissionTier
    extra = 0


@admin.register(CommissionPolicy)
class CommissionPolicyAdmin(admin.ModelAdmin):
    list_display = ["scope", "scope_ref_id", "percentage", "is_exempt", "effective_from", "effective_until"]
    list_filter = ["scope", "is_exempt", "requires_approval", "approved"]
    inlines = [CommissionTierInline]


@admin.register(CommissionCalculation)
class CommissionCalculationAdmin(admin.ModelAdmin):
    list_display = ["tenant_id", "reference_id", "commission_amount", "is_refund_reversal", "created_at"]
    list_filter = ["is_refund_reversal"]
    readonly_fields = [f.name for f in CommissionCalculation._meta.fields]

    def has_delete_permission(self, request, obj=None):
        return False  # immutable ledger
