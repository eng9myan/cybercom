from django.contrib import admin

from .models import SimulationRun


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ("scenario", "start_date", "days", "status", "seed",
                    "created_at", "completed_at")
    list_filter = ("scenario", "status")
    readonly_fields = ("scenario", "seed", "start_date", "days", "status",
                       "parameters", "summary", "record_counts", "completed_at",
                       "error", "created_at", "updated_at")
    search_fields = ("scenario",)

    def has_add_permission(self, request):
        return False
