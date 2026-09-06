from django.contrib import admin

from products.cycom.logistics.models import (
    DeliveryOrder, Package, Route, RouteStop, Shipment,
)
from products.cycom.manufacturing.models import ManufacturingOrder
from products.cycom.sales.models import SalesOrder

from .models import SimulationRun


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ("scenario", "start_date", "days", "status", "seed", "created_at", "completed_at")
    list_filter = ("scenario", "status")
    readonly_fields = [f.name for f in SimulationRun._meta.fields]

    def has_add_permission(self, request):
        return False


class _RO(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Shipment)
class ShipmentAdmin(_RO):
    list_display = ("number", "origin_country", "destination_country", "mode", "incoterm",
                    "status", "total_net_weight_kg", "total_gross_weight_kg", "total_packages")
    list_filter = ("status", "mode", "destination_country")
    search_fields = ("number",)


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(_RO):
    list_display = ("number", "customer_name", "destination_city", "status", "service_level",
                    "net_weight_kg", "gross_weight_kg", "package_count", "promised_date", "delivered_at")
    list_filter = ("status", "service_level", "destination_country")
    search_fields = ("number", "customer_name")


@admin.register(Package)
class PackageAdmin(_RO):
    list_display = ("package_no", "delivery_order", "packaging_type", "net_weight_kg",
                    "tare_weight_kg", "gross_weight_kg", "contents_description")


@admin.register(Route)
class RouteAdmin(_RO):
    list_display = ("name", "date", "driver_name", "vehicle_label", "status", "completed_stops",
                    "planned_stops", "actual_distance_km", "load_weight_kg")
    list_filter = ("status", "driver_name")


@admin.register(RouteStop)
class RouteStopAdmin(_RO):
    list_display = ("route", "sequence", "stop_type", "address", "status", "actual_arrival")
    list_filter = ("stop_type", "status")


@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(_RO):
    list_display = ("id", "bom", "quantity", "status", "scheduled_date", "reference")
    list_filter = ("status",)


@admin.register(SalesOrder)
class SalesOrderAdmin(_RO):
    list_display = ("number", "customer_name", "customer_type", "status", "amount_total",
                    "order_date", "salesperson")
    list_filter = ("status", "customer_type")
    search_fields = ("number", "customer_name")
