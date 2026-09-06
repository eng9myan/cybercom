from django.contrib import admin

from apps.hr.models import Employee
from apps.inventory.models import StockMovement
from apps.pos.models import PosOrder, PosOrderLine, PosSession
from apps.purchasing.models import PurchaseOrder

from .models import SimulationRun


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ("scenario", "start_date", "days", "status", "seed", "created_at", "completed_at")
    list_filter = ("scenario", "status")
    readonly_fields = [f.name for f in SimulationRun._meta.fields]

    def has_add_permission(self, request):
        return False


# ---- read-only views of the seeded operational data --------------------
class _RO(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PosOrder)
class PosOrderAdmin(_RO):
    list_display = ("order_number", "branch", "source", "daypart", "status",
                    "total", "placed_at", "served_at")
    list_filter = ("source", "daypart", "status", "branch")
    search_fields = ("order_number",)
    date_hierarchy = "placed_at"


@admin.register(PosSession)
class PosSessionAdmin(_RO):
    list_display = ("name", "branch", "cashier", "status", "opening_at", "closing_at")
    list_filter = ("status", "branch")


@admin.register(StockMovement)
class StockMovementAdmin(_RO):
    list_display = ("movement_type", "product", "quantity", "warehouse", "reference", "created_at")
    list_filter = ("movement_type", "warehouse")
    search_fields = ("reference", "product__name")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(_RO):
    list_display = ("po_number", "vendor", "branch", "status", "total", "order_date", "expected_date")
    list_filter = ("status",)


@admin.register(Employee)
class EmployeeAdmin(_RO):
    list_display = ("employee_id", "first_name", "last_name", "job_title", "branch", "status")
    list_filter = ("job_title", "status", "employment_type")
