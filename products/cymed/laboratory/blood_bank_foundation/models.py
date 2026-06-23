"""
CyMed Laboratory â€” Blood Bank Foundation
Foundation models only. Full Blood Bank (transfusion reactions, crossmatch
workflows, donor management, component preparation) is a future program.
"""
from django.db import models
from platform.common.models import BaseModel


class BloodGroup(models.TextChoices):
    A = "A", "A"
    B = "B", "B"
    AB = "AB", "AB"
    O = "O", "O"
    UNKNOWN = "unknown", "Unknown"


class RhType(models.TextChoices):
    POSITIVE = "positive", "Positive"
    NEGATIVE = "negative", "Negative"
    UNKNOWN = "unknown", "Unknown"


class BloodProductType(models.TextChoices):
    PRBC = "prbc", "Packed Red Blood Cells (PRBC)"
    FFP = "ffp", "Fresh Frozen Plasma (FFP)"
    PLATELETS = "platelets", "Platelet Concentrate"
    CRYO = "cryo", "Cryoprecipitate"
    WHOLE_BLOOD = "whole_blood", "Whole Blood"
    ALBUMIN = "albumin", "Albumin"
    IVIG = "ivig", "IVIG"


class BloodProduct(BaseModel):
    """Individual unit of blood product in inventory."""
    STATUS_CHOICES = [
        ("available", "Available"),
        ("reserved", "Reserved"),
        ("issued", "Issued"),
        ("transfused", "Transfused"),
        ("discarded", "Discarded"),
        ("quarantined", "Quarantined"),
        ("expired", "Expired"),
    ]

    unit_number = models.CharField(max_length=100, unique=True, db_index=True)
    product_type = models.CharField(max_length=20, choices=BloodProductType.choices)
    blood_group = models.CharField(max_length=10, choices=BloodGroup.choices, default=BloodGroup.UNKNOWN)
    rh_type = models.CharField(max_length=10, choices=RhType.choices, default=RhType.UNKNOWN)
    volume_ml = models.PositiveIntegerField(null=True, blank=True)
    collection_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    storage_location = models.CharField(max_length=100, blank=True)
    supplier = models.CharField(max_length=255, blank=True)
    special_attributes = models.JSONField(default=list)   # ["irradiated", "CMV_negative", "leukoreduced"]

    class Meta:
        db_table = "cymed_lab_blood_products"
        indexes = [
            models.Index(fields=["product_type", "blood_group", "rh_type", "status"]),
            models.Index(fields=["expiry_date", "status"]),
        ]


class BloodInventory(BaseModel):
    """Aggregate inventory counts by product type and blood group."""
    product_type = models.CharField(max_length=20, choices=BloodProductType.choices)
    blood_group = models.CharField(max_length=10, choices=BloodGroup.choices)
    rh_type = models.CharField(max_length=10, choices=RhType.choices)
    storage_location = models.CharField(max_length=100, blank=True)
    available_units = models.PositiveIntegerField(default=0)
    reserved_units = models.PositiveIntegerField(default=0)
    minimum_threshold = models.PositiveIntegerField(default=2)
    reorder_level = models.PositiveIntegerField(default=5)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymed_lab_blood_inventory"
        unique_together = [("tenant_id", "product_type", "blood_group", "rh_type", "storage_location")]


class BloodCompatibility(BaseModel):
    """Patient blood group and compatibility screening on file."""
    ANTIBODY_SCREEN_STATUS = [
        ("negative", "Negative"),
        ("positive", "Positive â€” Antibody Identified"),
        ("positive_pending", "Positive â€” Antibody Identification Pending"),
        ("not_done", "Not Done"),
    ]

    patient_id = models.UUIDField(db_index=True)
    blood_group = models.CharField(max_length=10, choices=BloodGroup.choices, default=BloodGroup.UNKNOWN)
    rh_type = models.CharField(max_length=10, choices=RhType.choices, default=RhType.UNKNOWN)
    antibody_screen = models.CharField(max_length=20, choices=ANTIBODY_SCREEN_STATUS, default="not_done")
    antibodies_identified = models.JSONField(default=list)     # ["Anti-E", "Anti-Kell"]
    special_requirements = models.JSONField(default=list)       # ["irradiated", "CMV_negative"]
    verified_by = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    sample_expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_blood_compatibility"
        indexes = [models.Index(fields=["patient_id", "verified_at"])]


class TransfusionRequest(BaseModel):
    """Request for blood product(s) for a patient."""
    URGENCY_CHOICES = [
        ("elective", "Elective"),
        ("urgent", "Urgent (2h)"),
        ("emergency", "Emergency (30min)"),
        ("massive_hemorrhage", "Massive Haemorrhage Protocol"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("crossmatch_ordered", "Crossmatch Ordered"),
        ("crossmatch_done", "Crossmatch Complete"),
        ("units_allocated", "Units Allocated"),
        ("issued", "Issued to Ward"),
        ("transfused", "Transfused"),
        ("cancelled", "Cancelled"),
    ]

    patient_id = models.UUIDField(db_index=True)
    order_item = models.ForeignKey(
        "lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="transfusion_requests", null=True, blank=True
    )
    product_type = models.CharField(max_length=20, choices=BloodProductType.choices)
    units_requested = models.PositiveSmallIntegerField(default=1)
    urgency = models.CharField(max_length=30, choices=URGENCY_CHOICES, default="elective")
    clinical_indication = models.CharField(max_length=500, blank=True)
    requested_by = models.UUIDField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    special_requirements = models.JSONField(default=list)
    requested_for_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_transfusion_requests"
        indexes = [models.Index(fields=["patient_id", "status"])]
