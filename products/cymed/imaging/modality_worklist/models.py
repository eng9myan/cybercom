from django.db import models
from platform.common.models import BaseModel


class Modality(BaseModel):
    class Meta:
        app_label = "img_worklist"
        db_table = "cymed_img_modalities"

    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=100)
    modality_type = models.CharField(max_length=20, choices=[
        ("xray", "X-Ray"), ("ct", "CT"), ("mri", "MRI"), ("us", "Ultrasound"),
        ("mg", "Mammography"), ("pet", "PET"), ("nm", "Nuclear Medicine"),
        ("fl", "Fluoroscopy"), ("xa", "Angiography"), ("dxa", "DEXA"),
    ])
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    ae_title = models.CharField(max_length=16, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    dicom_port = models.PositiveIntegerField(default=104)
    worklist_port = models.PositiveIntegerField(default=1050)
    is_active = models.BooleanField(default=True)
    location = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=100, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "img_worklist"
        db_table = "cymed_img_modalities"
        unique_together = [("tenant_id", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class ModalityWorklist(BaseModel):
    class Meta:
        app_label = "img_worklist"
        db_table = "cymed_img_modality_worklists"

    modality = models.ForeignKey("img_worklist.Modality", on_delete=models.CASCADE, related_name="worklists")
    worklist_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=[("open", "Open"), ("closed", "Closed")], default="open")
    created_by = models.UUIDField()
    total_entries = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.modality.code} — {self.worklist_date}"


class WorklistEntry(BaseModel):
    class Meta:
        app_label = "img_worklist"
        db_table = "cymed_img_worklist_entries"
        ordering = ["priority_rank", "scheduled_time"]

    worklist = models.ForeignKey("img_worklist.ModalityWorklist", on_delete=models.CASCADE, related_name="entries")
    order_item = models.ForeignKey("img_orders.ImagingOrderItem", on_delete=models.CASCADE)
    priority_rank = models.PositiveIntegerField(default=999)
    scheduled_time = models.TimeField(null=True, blank=True)
    patient_id = models.UUIDField()
    accession_number = models.CharField(max_length=100, blank=True)
    dicom_study_uid = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"), ("in_progress", "In Progress"),
        ("completed", "Completed"), ("cancelled", "Cancelled"),
    ], default="pending", db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    technologist_id = models.UUIDField(null=True, blank=True)
    images_acquired = models.PositiveIntegerField(default=0)
    dose_report = models.JSONField(default=dict)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Entry {self.id} — {self.status}"


class StudyQueue(BaseModel):
    class Meta:
        app_label = "img_worklist"
        db_table = "cymed_img_study_queue"
        ordering = ["position"]

    order_item = models.ForeignKey("img_orders.ImagingOrderItem", on_delete=models.CASCADE)
    queue_type = models.CharField(max_length=30, choices=[
        ("reading", "Reading"), ("qa", "QA"),
        ("critical", "Critical"), ("teleradiology", "Teleradiology"),
    ], default="reading")
    assigned_to = models.UUIDField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0, db_index=True)
    ai_priority_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_findings_summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="queued", db_index=True)

    def __str__(self):
        return f"Queue[{self.queue_type}] pos={self.position}"
