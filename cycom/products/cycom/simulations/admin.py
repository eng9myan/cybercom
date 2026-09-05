from django.contrib import admin

from .models import SimulationRun


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ("scenario", "start_date", "days", "status", "seed", "created_at", "completed_at")
    list_filter = ("scenario", "status")
    readonly_fields = [f.name for f in SimulationRun._meta.fields]

    def has_add_permission(self, request):
        return False
