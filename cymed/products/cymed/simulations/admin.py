from django.contrib import admin

from products.cymed.core.encounters.models import Encounter
from products.cymed.core.orders.models import Order
from products.cymed.core.scheduling.models import Appointment
from products.cymed.hospital.adt.models import Admission
from products.cymed.hospital.emergency.models import EmergencyVisit

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


@admin.register(EmergencyVisit)
class EmergencyVisitAdmin(_RO):
    # presenting_complaint is an encrypted PHI column — kept out of list/detail
    list_display = ("id", "arrival_method", "status", "arrival_time")
    list_filter = ("arrival_method", "status")
    exclude = ("presenting_complaint", "presenting_complaint_bidx")


@admin.register(Admission)
class AdmissionAdmin(_RO):
    list_display = ("id", "status", "admitted_at", "admission_type", "admission_reason")
    list_filter = ("status",)


@admin.register(Encounter)
class EncounterAdmin(_RO):
    list_display = ("id", "encounter_type", "status", "start_time", "end_time", "facility")
    list_filter = ("encounter_type", "status")


@admin.register(Appointment)
class AppointmentAdmin(_RO):
    list_display = ("id", "appointment_type", "status", "start_time", "end_time")
    list_filter = ("status", "appointment_type")


@admin.register(Order)
class OrderAdmin(_RO):
    list_display = ("id", "order_type", "priority", "status", "ordered_by", "ordered_at")
    list_filter = ("order_type", "priority", "status")
