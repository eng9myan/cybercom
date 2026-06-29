"""
CyMed Laboratory â€” Reference Lab Network
Cross-lab routing, referral testing, multi-lab operations, national network.
"""

from django.db import models

from platform.common.models import BaseModel


class IntegrationType(models.TextChoices):
    FHIR = "fhir", "FHIR R4 API"
    HL7 = "hl7", "HL7 v2.x (via CyIntegrationHub)"
    FLAT_FILE = "flat_file", "Flat File (CSV/Excel)"
    API_REST = "api_rest", "REST API"
    MANUAL = "manual", "Manual Entry"


class ReferenceLab(BaseModel):
    """External or internal reference laboratory for test referral."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("pending", "Pending Onboarding"),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=5, default="SA")
    city = models.CharField(max_length=100, blank=True)
    integration_type = models.CharField(max_length=20, choices=IntegrationType.choices)
    api_endpoint = models.URLField(max_length=500, blank=True)
    api_key_reference = models.CharField(max_length=255, blank=True)  # secret manager key name
    fhir_base_url = models.URLField(max_length=500, blank=True)
    integration_hub_channel = models.CharField(max_length=100, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    sla_tat_hours = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    is_national = models.BooleanField(default=False)
    is_government = models.BooleanField(default=False)
    certifications = models.JSONField(default=list)  # ["ISO15189", "CAP", "MOH"]

    class Meta:
        db_table = "cymed_lab_reference_labs"

    def __str__(self):
        return f"{self.code} â€” {self.name}"


class ReferenceLabRouting(BaseModel):
    """Rule: route a specific test to a specific reference lab when conditions are met."""

    test = models.ForeignKey(
        "lab_orders.LabTest", on_delete=models.CASCADE, related_name="routing_rules"
    )
    reference_lab = models.ForeignKey(
        ReferenceLab, on_delete=models.CASCADE, related_name="routing_rules"
    )
    is_default = models.BooleanField(default=False)
    conditions = models.JSONField(
        default=dict
    )  # {"priority": "stat", "test_unavailable_locally": true}
    estimated_tat_hours = models.PositiveIntegerField(null=True, blank=True)
    priority_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_until = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_reference_routing"
        ordering = ["test", "priority_order"]


class ReferenceLabOrder(BaseModel):
    """A test order sent to a reference lab for processing."""

    STATUS_CHOICES = [
        ("pending", "Pending Dispatch"),
        ("sent", "Sent to Reference Lab"),
        ("received", "Received by Reference Lab"),
        ("in_progress", "In Progress"),
        ("resulted", "Result Received"),
        ("imported", "Result Imported"),
        ("failed", "Failed â€” Intervention Required"),
        ("cancelled", "Cancelled"),
    ]

    local_order_item = models.ForeignKey(
        "lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="reference_lab_orders"
    )
    reference_lab = models.ForeignKey(ReferenceLab, on_delete=models.PROTECT, related_name="orders")
    external_order_id = models.CharField(max_length=255, blank=True)
    external_accession_number = models.CharField(max_length=100, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    expected_result_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    dispatch_method = models.CharField(max_length=30, blank=True)  # courier, electronic
    specimen_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_reference_orders"
        indexes = [models.Index(fields=["reference_lab", "status", "sent_at"])]


class ReferenceLabResult(BaseModel):
    """Result received from a reference lab, parsed and ready for import."""

    STATUS_CHOICES = [
        ("received", "Raw Result Received"),
        ("parsed", "Parsed Successfully"),
        ("imported", "Imported to LIS Result"),
        ("parse_error", "Parse Error"),
        ("import_error", "Import Error"),
    ]

    reference_lab_order = models.OneToOneField(
        ReferenceLabOrder, on_delete=models.CASCADE, related_name="result"
    )
    raw_result = models.JSONField(default=dict)  # raw payload from reference lab
    raw_format = models.CharField(max_length=20, blank=True)  # fhir, hl7, json, pdf
    received_at = models.DateTimeField(auto_now_add=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)
    imported_by = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="received")
    error_detail = models.TextField(blank=True)
    linked_result_id = models.UUIDField(null=True, blank=True)  # FK to results.LabResult

    class Meta:
        db_table = "cymed_lab_reference_results"
