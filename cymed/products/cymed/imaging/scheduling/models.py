from django.db import models

from platform.common.models import BaseModel

APPOINTMENT_STATUSES = [
    ("scheduled", "Scheduled"),
    ("confirmed", "Confirmed"),
    ("arrived", "Arrived"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
    ("no_show", "No Show"),
    ("rescheduled", "Rescheduled"),
]


class ImagingRoom(BaseModel):
    class Meta:
        app_label = "img_scheduling"
        db_table = "cymed_img_rooms"

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    modality_type = models.CharField(max_length=20)
    building = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=20, blank=True)
    shielding_type = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} — {self.name}"


class ImagingAppointment(BaseModel):
    class Meta:
        app_label = "img_scheduling"
        db_table = "cymed_img_appointments"

    order_item = models.OneToOneField(
        "img_orders.ImagingOrderItem", on_delete=models.CASCADE, related_name="appointment"
    )
    patient_id = models.UUIDField(db_index=True)
    modality = models.ForeignKey("img_worklist.Modality", on_delete=models.PROTECT)
    radiologist_id = models.UUIDField(null=True, blank=True)
    technologist_id = models.UUIDField(null=True, blank=True)
    room = models.ForeignKey(
        "img_scheduling.ImagingRoom", null=True, blank=True, on_delete=models.SET_NULL
    )
    scheduled_start = models.DateTimeField(db_index=True)
    scheduled_end = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=APPOINTMENT_STATUSES, default="scheduled", db_index=True
    )
    patient_arrived_at = models.DateTimeField(null=True, blank=True)
    exam_started_at = models.DateTimeField(null=True, blank=True)
    exam_completed_at = models.DateTimeField(null=True, blank=True)
    check_in_notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)
    contrast_pre_screening = models.JSONField(default=dict)

    def __str__(self):
        return f"Appt {self.id} — {self.scheduled_start}"


class ModalitySchedule(BaseModel):
    class Meta:
        app_label = "img_scheduling"
        db_table = "cymed_img_modality_schedule"
        unique_together = [("modality", "schedule_date")]

    modality = models.ForeignKey(
        "img_worklist.Modality", on_delete=models.CASCADE, related_name="schedules"
    )
    schedule_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    available_slots = models.PositiveIntegerField(default=0)
    booked_slots = models.PositiveIntegerField(default=0)
    is_blocked = models.BooleanField(default=False)
    downtime_reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.modality.code} — {self.schedule_date}"


class RadiologistSchedule(BaseModel):
    class Meta:
        app_label = "img_scheduling"
        db_table = "cymed_img_radiologist_schedule"

    radiologist_id = models.UUIDField(db_index=True)
    schedule_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    modality_types = models.JSONField(default=list)
    subspecialty = models.CharField(max_length=100, blank=True)
    is_on_call = models.BooleanField(default=False)
    is_teleradiology = models.BooleanField(default=False)
    site_code = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Rad {self.radiologist_id} — {self.schedule_date}"
