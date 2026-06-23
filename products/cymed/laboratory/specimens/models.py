"""
CyMed Laboratory â€” Specimen Management
Covers: Specimen, SpecimenContainer, SpecimenCollection, SpecimenTransport,
        SpecimenStorage, SpecimenRejection, SpecimenChainOfCustody
Barcode + QR tracking, full chain of custody, rejection workflows.
"""
from django.db import models
from platform.common.models import BaseModel


class SpecimenStatus(models.TextChoices):
    PENDING = "pending", "Pending Collection"
    COLLECTED = "collected", "Collected"
    IN_TRANSIT = "in_transit", "In Transit"
    RECEIVED = "received", "Received"
    ACCESSIONED = "accessioned", "Accessioned"
    IN_PROCESSING = "in_processing", "In Processing"
    STORED = "stored", "In Storage"
    REJECTED = "rejected", "Rejected"
    DISPOSED = "disposed", "Disposed"


class Specimen(BaseModel):
    """Core specimen record tracking a physical sample throughout its lifecycle."""
    specimen_number = models.CharField(max_length=100, unique=True, db_index=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True)
    qr_code = models.CharField(max_length=255, blank=True)
    order_item = models.OneToOneField(
        "lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="specimen", null=True, blank=True
    )
    patient_id = models.UUIDField(db_index=True)
    specimen_type = models.CharField(max_length=100)       # blood, serum, urine, CSF, etc.
    snomed_specimen_code = models.CharField(max_length=50, blank=True)  # SNOMED-CT via TerminologyService
    collection_site = models.CharField(max_length=200, blank=True)
    volume_ml = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    container_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=SpecimenStatus.choices, default=SpecimenStatus.PENDING)
    collected_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    fhir_specimen_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_lab_specimens"
        indexes = [
            models.Index(fields=["patient_id", "status"]),
            models.Index(fields=["tenant_id", "specimen_type"]),
        ]

    def __str__(self):
        return f"{self.specimen_number} ({self.specimen_type})"


class SpecimenContainer(BaseModel):
    """Physical container holding one or more aliquots of a specimen."""
    CONTAINER_TYPES = [
        ("edta", "EDTA Purple Top"),
        ("sst", "SST Gold Top"),
        ("plain", "Plain Red Top"),
        ("citrate", "Sodium Citrate Blue Top"),
        ("heparin", "Lithium Heparin Green Top"),
        ("fluoride", "Sodium Fluoride Grey Top"),
        ("urine_cup", "Urine Cup"),
        ("sterile_jar", "Sterile Jar"),
        ("swab", "Swab"),
        ("slide", "Glass Slide"),
        ("cassette", "Tissue Cassette"),
        ("blood_culture", "Blood Culture Bottle"),
        ("csf_tube", "CSF Collection Tube"),
    ]

    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, related_name="containers")
    container_type = models.CharField(max_length=50, choices=CONTAINER_TYPES)
    barcode = models.CharField(max_length=100, unique=True)
    volume_ml = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    is_primary = models.BooleanField(default=True)
    is_aliquot = models.BooleanField(default=False)
    aliquot_of = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="aliquots")
    label_printed = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_specimen_containers"


class SpecimenCollection(BaseModel):
    """Records the collection event for a specimen."""
    specimen = models.OneToOneField(Specimen, on_delete=models.CASCADE, related_name="collection")
    collected_by = models.UUIDField()                       # provider/phlebotomist id
    collected_at = models.DateTimeField()
    collection_site = models.CharField(max_length=200)
    collection_method = models.CharField(max_length=100, blank=True)
    patient_fasting = models.BooleanField(default=False)
    fasting_hours = models.PositiveSmallIntegerField(null=True, blank=True)
    collection_notes = models.TextField(blank=True)
    collection_device = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_lab_specimen_collections"


class SpecimenTransport(BaseModel):
    """Tracks specimen transport between locations."""
    STATUS_CHOICES = [
        ("dispatched", "Dispatched"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("failed", "Failed â€” Specimen Issue"),
    ]

    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, related_name="transports")
    from_location = models.CharField(max_length=255)
    to_location = models.CharField(max_length=255)
    transported_by = models.UUIDField(null=True, blank=True)
    dispatched_at = models.DateTimeField()
    received_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="dispatched")
    temperature_celsius = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, blank=True)
    transport_notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_specimen_transports"


class SpecimenStorage(BaseModel):
    """Tracks storage location, temperature, and retention of a specimen."""
    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, related_name="storage_records")
    location_code = models.CharField(max_length=100)        # e.g., "FRIDGE-03-SHELF-B-RACK-2"
    location_description = models.CharField(max_length=255, blank=True)
    temperature_celsius = models.DecimalField(max_digits=5, decimal_places=1)
    stored_at = models.DateTimeField()
    stored_by = models.UUIDField(null=True, blank=True)
    scheduled_disposal_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_lab_specimen_storage"
        indexes = [models.Index(fields=["specimen", "is_current"])]


class SpecimenRejection(BaseModel):
    """Records specimen rejection with reason and follow-up action."""
    REJECTION_REASONS = [
        ("quantity_insufficient", "Quantity Not Sufficient (QNS)"),
        ("hemolyzed", "Hemolyzed"),
        ("lipemic", "Lipemic"),
        ("icteric", "Icteric"),
        ("clotted", "Clotted"),
        ("wrong_container", "Wrong Container Type"),
        ("mislabeled", "Mislabeled"),
        ("expired_container", "Expired Container"),
        ("improper_storage", "Improper Storage/Transport Temperature"),
        ("contaminated", "Contaminated"),
        ("broken", "Broken Container"),
        ("wrong_test", "Wrong Test Requested"),
        ("no_request", "No Request/Requisition"),
        ("other", "Other"),
    ]
    ACTION_TAKEN = [
        ("recollect", "Recollect"),
        ("partial_result", "Partial Result Reported"),
        ("add_comment", "Add Comment and Process"),
        ("cancel_order", "Cancel Order Item"),
    ]

    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, related_name="rejections")
    rejection_reason = models.CharField(max_length=50, choices=REJECTION_REASONS)
    rejection_details = models.TextField(blank=True)
    rejected_by = models.UUIDField()
    rejected_at = models.DateTimeField(auto_now_add=True)
    action_taken = models.CharField(max_length=30, choices=ACTION_TAKEN, blank=True)
    notified_provider = models.UUIDField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_specimen_rejections"


class SpecimenChainOfCustody(BaseModel):
    """Immutable chain-of-custody log for medico-legal and forensic traceability."""
    CUSTODY_ACTIONS = [
        ("collected", "Collected"),
        ("labeled", "Labeled"),
        ("packaged", "Packaged"),
        ("transferred", "Transferred"),
        ("received", "Received"),
        ("accessioned", "Accessioned"),
        ("aliquoted", "Aliquoted"),
        ("processed", "Processed"),
        ("stored", "Stored"),
        ("retrieved", "Retrieved from Storage"),
        ("disposed", "Disposed"),
        ("sent_external", "Sent to External Lab"),
    ]

    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, related_name="chain_of_custody")
    action = models.CharField(max_length=30, choices=CUSTODY_ACTIONS)
    performed_by = models.UUIDField()
    location = models.CharField(max_length=255, blank=True)
    action_timestamp = models.DateTimeField()
    notes = models.CharField(max_length=500, blank=True)
    digital_signature = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = "cymed_lab_specimen_chain_of_custody"
        ordering = ["action_timestamp"]
