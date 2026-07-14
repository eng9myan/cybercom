from django.contrib import admin

from .models import DeliveryCompany, DeliveryJob, Driver, Vehicle


@admin.register(DeliveryCompany)
class DeliveryCompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "network_status", "cydrive_subscription_active", "created_at"]
    list_filter = ["network_status", "cydrive_subscription_active"]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "company", "vehicle_type", "is_active", "is_compliant"]
    list_filter = ["vehicle_type", "is_active"]


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "status", "rating", "zone"]
    list_filter = ["status"]


@admin.register(DeliveryJob)
class DeliveryJobAdmin(admin.ModelAdmin):
    list_display = ["id", "company", "driver", "status", "created_at"]
    list_filter = ["status"]
