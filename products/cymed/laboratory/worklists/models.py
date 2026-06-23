"""
CyMed Laboratory â€” Worklist Engine
Department/priority/STAT/analyzer worklists with technologist assignment.
Includes Analyzer framework for instrument connectivity via CyIntegrationHub.
"""
from django.db import models
from platform.common.models import BaseModel


class Department(models.TextChoices):
    CHEMISTRY = "chemistry", "Chemistry"
    HEMATOLOGY = "hematology", "Hematology"
    IMMUNOLOGY = "immunology", "Immunology"
    SEROLOGY = "serology", "Serology"
    MICROBIOLOGY = "microbiology", "Microbiology"
    PATHOLOGY = "pathology", "Pathology"
    HISTOPATHOLOGY = "histopathology", "Histopathology"
    MOLECULAR = "molecular", "Molecular Diagnostics"
    BLOOD_BANK = "blood_bank", "Blood Bank"
    URINALYSIS = "urinalysis", "Urinalysis"


class Analyzer(BaseModel):
    """Physical or virtual laboratory instrument. Communication via CyIntegrationHub."""
    ANALYZER_TYPES = [
        ("chemistry", "Chemistry Analyzer"),
        ("hematology", "Hematology Analyzer"),
        ("immunology", "Immunology/Immunoassay Analyzer"),
        ("microbiology", "Microbiology MALDI-TOF"),
        ("coagulation", "Coagulation Analyzer"),
        ("urinalysis", "Urinalysis Analyzer"),
        ("molecular", "Molecular PCR Analyzer"),
        ("point_of_care", "Point-of-Care Device"),
        ("blood_gas", "Blood Gas Analyzer"),
        ("flow_cytometry", "Flow Cytometry"),
    ]
    PROTOCOL_TYPES = [
        ("astm", "ASTM 1394/1381"),
        ("hl7", "HL7 v2.x"),
        ("lis_interface", "Vendor LIS Interface"),
        ("serial", "Serial RS-232"),
        ("fhir", "FHIR R4"),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    analyzer_type = models.CharField(max_length=30, choices=ANALYZER_TYPES)
    department = models.CharField(max_length=30, choices=Department.choices)
    location = models.CharField(max_length=255, blank=True)
    integration_hub_channel = models.CharField(max_length=100, blank=True)
    protocol = models.CharField(max_length=30, choices=PROTOCOL_TYPES, blank=True)
    is_active = models.BooleanField(default=True)
    last_calibrated_at = models.DateTimeField(null=True, blank=True)
    last_qc_at = models.DateTimeField(null=True, blank=True)
    asset_id = models.CharField(max_length=100, blank=True)  # CyCom ERP asset reference

    class Meta:
        db_table = "cymed_lab_analyzers"

    def __str__(self):
        return f"{self.code} â€” {self.name}"


class AnalyzerInterface(BaseModel):
    """Test-to-analyzer routing: maps a LabTest to an Analyzer with instrument test codes."""
    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE, related_name="interfaces")
    test = models.ForeignKey("lab_orders.LabTest", on_delete=models.CASCADE, related_name="analyzer_interfaces")
    instrument_test_code = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=True)
    priority_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_analyzer_interfaces"
        unique_together = [("analyzer", "test")]


class AnalyzerMessage(BaseModel):
    """Raw message received from or sent to an analyzer via CyIntegrationHub."""
    DIRECTIONS = [("inbound", "From Analyzer"), ("outbound", "To Analyzer")]
    STATUS_CHOICES = [
        ("received", "Received"),
        ("processing", "Processing"),
        ("processed", "Processed"),
        ("failed", "Failed"),
        ("ignored", "Ignored"),
    ]

    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=10, choices=DIRECTIONS)
    message_type = models.CharField(max_length=20, blank=True)   # ORM, ORU, QRY, etc.
    raw_message = models.TextField()
    parsed_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="received")
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_detail = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_analyzer_messages"
        indexes = [models.Index(fields=["analyzer", "status", "received_at"])]


class AnalyzerResult(BaseModel):
    """Result received from analyzer, pending validation and linkage to LabResult."""
    message = models.ForeignKey(AnalyzerMessage, on_delete=models.CASCADE, related_name="analyzer_results")
    analyzer = models.ForeignKey(Analyzer, on_delete=models.PROTECT, related_name="raw_results")
    instrument_test_code = models.CharField(max_length=100)
    instrument_sample_id = models.CharField(max_length=100, blank=True)
    accession_number = models.CharField(max_length=100, blank=True, db_index=True)
    value_raw = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)
    flags = models.CharField(max_length=20, blank=True)    # H, L, HH, LL, A, etc.
    instrument_range_low = models.CharField(max_length=50, blank=True)
    instrument_range_high = models.CharField(max_length=50, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    lab_result_linked = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_analyzer_results"


class LabWorklist(BaseModel):
    """A sorted list of order items queued for a department/analyzer on a given date."""
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    PRIORITY_MODES = [
        ("fifo", "First In First Out"),
        ("priority_first", "Priority First (STAT/Urgent)"),
        ("timed", "Timed Collection"),
        ("analyzer_batch", "Analyzer Batch"),
    ]

    name = models.CharField(max_length=255)
    department = models.CharField(max_length=30, choices=Department.choices)
    analyzer = models.ForeignKey(Analyzer, on_delete=models.SET_NULL, null=True, blank=True, related_name="worklists")
    worklist_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    priority_mode = models.CharField(max_length=20, choices=PRIORITY_MODES, default="priority_first")
    created_by = models.UUIDField()
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_worklists"
        indexes = [models.Index(fields=["tenant_id", "department", "worklist_date"])]

    def __str__(self):
        return f"{self.name} ({self.worklist_date})"


class WorklistItem(BaseModel):
    """Individual test-item assignment on a worklist."""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("resulted", "Resulted"),
        ("verified", "Verified"),
        ("cancelled", "Cancelled"),
    ]

    worklist = models.ForeignKey(LabWorklist, on_delete=models.CASCADE, related_name="items")
    order_item = models.ForeignKey("lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="worklist_items")
    sequence = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    technologist_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_worklist_items"
        ordering = ["worklist", "sequence"]
        unique_together = [("worklist", "order_item")]


class WorklistQueue(BaseModel):
    """Analyzer queue depth monitoring â€” how many items are queued on each analyzer."""
    worklist = models.ForeignKey(LabWorklist, on_delete=models.CASCADE, related_name="queues")
    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE, related_name="queue_records")
    queue_depth = models.PositiveIntegerField(default=0)
    estimated_completion_minutes = models.PositiveIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymed_lab_worklist_queues"
        unique_together = [("worklist", "analyzer")]


class TechnologistAssignment(BaseModel):
    """Assigns a technologist to cover a worklist or a section of it."""
    STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("reassigned", "Reassigned"),
    ]

    worklist = models.ForeignKey(LabWorklist, on_delete=models.CASCADE, related_name="technologist_assignments")
    technologist_id = models.UUIDField()
    assigned_by = models.UUIDField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="assigned")
    items_target = models.PositiveIntegerField(default=0)
    items_completed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_technologist_assignments"
