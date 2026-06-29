from django.db import models

from platform.common.models import BaseModel


class ModalityType(models.TextChoices):
    XRAY = "xray", "X-Ray"
    CT = "ct", "CT"
    MRI = "mri", "MRI"
    ULTRASOUND = "us", "Ultrasound"
    MAMMOGRAPHY = "mg", "Mammography"
    PET = "pet", "PET"
    NUCLEAR = "nm", "Nuclear Medicine"
    FLUOROSCOPY = "fl", "Fluoroscopy"
    ANGIOGRAPHY = "xa", "Angiography"
    DEXA = "dxa", "DEXA"


class ImagingPriority(models.TextChoices):
    ROUTINE = "routine", "Routine"
    URGENT = "urgent", "Urgent"
    STAT = "stat", "STAT"
    CRITICAL = "critical", "Critical"


ORDER_TYPES = [
    ("outpatient", "Outpatient"),
    ("inpatient", "Inpatient"),
    ("emergency", "Emergency"),
    ("scheduled", "Scheduled"),
    ("teleradiology", "Teleradiology"),
]

ORDER_STATUSES = [
    ("pending", "Pending"),
    ("scheduled", "Scheduled"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
    ("on_hold", "On Hold"),
]


class ImagingProtocol(BaseModel):
    class Meta:
        app_label = "img_orders"
        db_table = "cymed_img_protocols"

    name = models.CharField(max_length=255)
    modality = models.CharField(max_length=20, choices=ModalityType.choices)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict)
    contrast_phases = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ImagingProcedure(BaseModel):
    code = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    modality = models.CharField(max_length=20, choices=ModalityType.choices)
    snomed_code = models.CharField(max_length=20, blank=True, db_index=True)
    loinc_code = models.CharField(max_length=20, blank=True, db_index=True)
    body_part = models.CharField(max_length=100, blank=True)
    laterality = models.CharField(max_length=20, blank=True)
    protocol = models.ForeignKey(
        "img_orders.ImagingProtocol", null=True, blank=True, on_delete=models.SET_NULL
    )
    preparation_instructions = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    contrast_required = models.BooleanField(default=False)
    radiation_dose_estimate = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True
    )
    rvu_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "img_orders"
        db_table = "cymed_img_procedures"
        unique_together = [("tenant_id", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class ImagingOrder(BaseModel):
    class Meta:
        app_label = "img_orders"
        db_table = "cymed_img_orders"

    order_number = models.CharField(max_length=100, unique=True)
    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(null=True, blank=True, db_index=True)
    ordered_by = models.UUIDField()
    priority = models.CharField(
        max_length=20, choices=ImagingPriority.choices, default=ImagingPriority.ROUTINE
    )
    order_type = models.CharField(max_length=30, choices=ORDER_TYPES, default="outpatient")
    clinical_indication = models.TextField(blank=True)
    icd11_codes = models.JSONField(default=list)
    fhir_service_request_id = models.CharField(max_length=255, blank=True)
    hl7_placer_order_number = models.CharField(max_length=100, blank=True)
    hl7_filler_order_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=30, choices=ORDER_STATUSES, default="pending", db_index=True
    )
    ordering_facility = models.CharField(max_length=255, blank=True)
    transport_required = models.BooleanField(default=False)
    is_portable = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.order_number


class ImagingOrderItem(BaseModel):
    class Meta:
        app_label = "img_orders"
        db_table = "cymed_img_order_items"

    ITEM_STATUSES = [
        ("pending", "Pending"),
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    LATERALITY = [
        ("left", "Left"),
        ("right", "Right"),
        ("bilateral", "Bilateral"),
        ("none", "None"),
    ]

    order = models.ForeignKey(
        "img_orders.ImagingOrder", on_delete=models.CASCADE, related_name="items"
    )
    procedure = models.ForeignKey("img_orders.ImagingProcedure", on_delete=models.PROTECT)
    body_part = models.CharField(max_length=100, blank=True)
    laterality = models.CharField(max_length=20, choices=LATERALITY, blank=True)
    contrast_required = models.BooleanField(default=False)
    status = models.CharField(
        max_length=30, choices=ITEM_STATUSES, default="pending", db_index=True
    )
    dicom_study_instance_uid = models.CharField(max_length=255, blank=True, db_index=True)
    accession_number = models.CharField(max_length=100, blank=True, db_index=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order.order_number}/{self.procedure.code}"


class ImagingOrderStatusHistory(BaseModel):
    class Meta:
        app_label = "img_orders"
        db_table = "cymed_img_order_status_history"
        ordering = ["changed_at"]

    order = models.ForeignKey(
        "img_orders.ImagingOrder", on_delete=models.CASCADE, related_name="status_history"
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.UUIDField()
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} → {self.to_status}"
