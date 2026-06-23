from django.db import models
from platform.common.models import BaseModel

IMAGING_PRIORITIES = [
    ("routine", "Routine"), ("urgent", "Urgent"),
    ("stat", "STAT"), ("critical", "Critical"),
]


class ReadingQueue(BaseModel):
    class Meta:
        app_label = "img_teleradiology"
        db_table = "cymed_img_reading_queues"

    name = models.CharField(max_length=100)
    queue_type = models.CharField(max_length=30, choices=[
        ("general", "General"), ("subspecialty", "Subspecialty"),
        ("urgent", "Urgent"), ("night_hawk", "Night Hawk"),
        ("second_opinion", "Second Opinion"),
    ], default="general")
    subspecialty = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    max_turnaround_hours = models.PositiveIntegerField(default=24)
    site_code = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class TeleradiologyCase(BaseModel):
    class Meta:
        app_label = "img_teleradiology"
        db_table = "cymed_img_teleradiology_cases"

    order_item = models.ForeignKey("img_orders.ImagingOrderItem", on_delete=models.CASCADE)
    study = models.ForeignKey(
        "img_dicom.DICOMStudy", null=True, blank=True, on_delete=models.SET_NULL
    )
    reading_queue = models.ForeignKey(
        "img_teleradiology.ReadingQueue", null=True, blank=True, on_delete=models.SET_NULL
    )
    case_type = models.CharField(max_length=30, choices=[
        ("primary", "Primary Read"), ("second_opinion", "Second Opinion"),
        ("consultation", "Consultation"), ("urgent", "Urgent Read"),
    ], default="primary")
    originating_facility = models.CharField(max_length=255, blank=True)
    originating_site_code = models.CharField(max_length=50, blank=True)
    target_turnaround_hours = models.PositiveIntegerField(default=24)
    priority = models.CharField(max_length=20, choices=IMAGING_PRIORITIES, default="routine")
    status = models.CharField(max_length=30, choices=[
        ("pending", "Pending"), ("assigned", "Assigned"),
        ("in_progress", "In Progress"), ("completed", "Completed"), ("cancelled", "Cancelled"),
    ], default="pending", db_index=True)
    clinical_context = models.TextField(blank=True)
    patient_history = models.TextField(blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TeleCase {self.id} — {self.case_type}"


class ReadingAssignment(BaseModel):
    class Meta:
        app_label = "img_teleradiology"
        db_table = "cymed_img_reading_assignments"

    teleradiology_case = models.ForeignKey(
        "img_teleradiology.TeleradiologyCase", on_delete=models.CASCADE, related_name="assignments"
    )
    radiologist_id = models.UUIDField()
    subspecialty = models.CharField(max_length=100, blank=True)
    assigned_by = models.UUIDField()
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ("assigned", "Assigned"), ("accepted", "Accepted"),
        ("in_progress", "In Progress"), ("completed", "Completed"), ("rejected", "Rejected"),
    ], default="assigned", db_index=True)
    rejection_reason = models.TextField(blank=True)
    turnaround_minutes = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Assignment {self.id} — {self.status}"


class SecondOpinion(BaseModel):
    class Meta:
        app_label = "img_teleradiology"
        db_table = "cymed_img_second_opinions"

    original_report = models.ForeignKey("img_reporting.RadiologyReport", on_delete=models.CASCADE)
    requested_by = models.UUIDField()
    second_opinion_radiologist_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField()
    clinical_question = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"), ("assigned", "Assigned"),
        ("in_progress", "In Progress"), ("completed", "Completed"),
    ], default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    opinion_text = models.TextField(blank=True)
    concurs_with_original = models.BooleanField(null=True)
    discrepancy_level = models.CharField(max_length=20, choices=[
        ("none", "None"), ("minor", "Minor"), ("major", "Major"),
    ], blank=True)

    def __str__(self):
        return f"SecondOpinion {self.id} — {self.status}"
