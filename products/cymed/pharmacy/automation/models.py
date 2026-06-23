"""
CyMed Pharmacy — Pharmacy Automation Module
Models: AutomationDevice, DispensingRobot, CabinetDevice, AutomationQueue

Capabilities: ADC Integration, Cabinet Integration, Dispensing Robot Integration,
              Smart Storage Integration

ALL external device integrations route through CyIntegrationHub (Program 2.6).
No direct device communication in this module.
"""
from django.db import models
from platform.common.models import BaseModel


class DeviceType(models.TextChoices):
    ADC = "adc", "Automated Dispensing Cabinet (ADC)"
    DISPENSING_ROBOT = "robot", "Dispensing Robot"
    SMART_CABINET = "smart_cabinet", "Smart Storage Cabinet"
    CAROUSEL = "carousel", "Vertical Carousel"
    PYXIS = "pyxis", "BD Pyxis"
    OMNICELL = "omnicell", "Omnicell"
    SWISSLOG = "swisslog", "Swisslog"
    CUSTOM = "custom", "Custom Device"


class DeviceStatus(models.TextChoices):
    ONLINE = "online", "Online"
    OFFLINE = "offline", "Offline"
    MAINTENANCE = "maintenance", "Under Maintenance"
    ERROR = "error", "Error"
    SYNCING = "syncing", "Syncing"


class AutomationDevice(BaseModel):
    """
    Master registry of all pharmacy automation devices.
    Device communication is handled exclusively via CyIntegrationHub (Program 2.6).
    This record is the platform-side reference — not the device controller.
    """
    device_code = models.CharField(max_length=100, unique=True, db_index=True)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=30, choices=DeviceType.choices)
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)

    # Location
    facility_id = models.UUIDField(null=True, blank=True)
    location = models.CharField(max_length=255)                       # e.g., "ICU Level 3, Bay 2"
    ward_id = models.UUIDField(null=True, blank=True)

    # CyIntegrationHub reference
    integration_hub_device_id = models.CharField(max_length=255, blank=True)  # Hub device ID
    integration_hub_endpoint = models.CharField(max_length=500, blank=True)

    # Status
    status = models.CharField(max_length=30, choices=DeviceStatus.choices, default=DeviceStatus.OFFLINE)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    # Capabilities
    supports_barcode = models.BooleanField(default=True)
    supports_biometric = models.BooleanField(default=False)
    pocket_count = models.PositiveSmallIntegerField(default=0)
    controlled_substance_capable = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_automation_devices"
        indexes = [
            models.Index(fields=["tenant_id", "device_type", "status"]),
            models.Index(fields=["facility_id", "ward_id"]),
        ]

    def __str__(self):
        return f"{self.device_name} ({self.get_device_type_display()})"


class DispensingRobot(BaseModel):
    """
    Extended profile for dispensing robot devices (e.g., Swisslog, Omnicell).
    References the AutomationDevice master record.
    All robot commands route through CyIntegrationHub.
    """
    device = models.OneToOneField(
        AutomationDevice, on_delete=models.CASCADE, related_name="robot_profile"
    )
    dispensing_speed = models.PositiveSmallIntegerField(default=0)    # items/hour
    storage_capacity = models.PositiveIntegerField(default=0)         # unique drugs
    supports_iv_admixture = models.BooleanField(default=False)
    supports_unit_dose = models.BooleanField(default=True)
    supports_blister_pack = models.BooleanField(default=False)
    robot_hl7_endpoint = models.CharField(max_length=500, blank=True)
    robot_api_version = models.CharField(max_length=20, blank=True)
    last_calibrated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_dispensing_robots"


class CabinetDevice(BaseModel):
    """
    Extended profile for ADC / smart cabinet devices (e.g., BD Pyxis, Omnicell).
    All cabinet commands route through CyIntegrationHub.
    """
    device = models.OneToOneField(
        AutomationDevice, on_delete=models.CASCADE, related_name="cabinet_profile"
    )
    cabinet_type = models.CharField(
        max_length=30,
        choices=[
            ("adc", "Automated Dispensing Cabinet"),
            ("narcotic_safe", "Controlled Substance Safe"),
            ("refrigerated", "Refrigerated Cabinet"),
            ("chemotherapy", "Chemotherapy Cabinet"),
        ],
        default="adc"
    )
    slot_count = models.PositiveSmallIntegerField(default=0)
    is_networked = models.BooleanField(default=True)
    requires_biometric = models.BooleanField(default=False)
    requires_witness = models.BooleanField(default=False)             # For controlled substances
    restocking_alert_threshold = models.PositiveSmallIntegerField(default=20)  # % remaining
    assigned_formulary_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_cabinet_devices"


class AutomationQueue(BaseModel):
    """
    Queue of dispense requests routed to automation devices.
    CyIntegrationHub picks up and executes the actual device commands.
    """
    QUEUE_STATUS = [
        ("pending", "Pending"),
        ("sent_to_hub", "Sent to CyIntegrationHub"),
        ("accepted", "Device Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("timeout", "Timeout"),
    ]

    dispense_order_id = models.UUIDField(db_index=True)              # FK to DispenseOrder
    device = models.ForeignKey(
        AutomationDevice, on_delete=models.PROTECT, related_name="queue_items"
    )
    drug_code = models.CharField(max_length=100)
    drug_name = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_unit = models.CharField(max_length=50)

    status = models.CharField(max_length=30, choices=QUEUE_STATUS, default="pending")

    # CyIntegrationHub tracking
    hub_request_id = models.CharField(max_length=255, blank=True)
    hub_response = models.JSONField(default=dict)
    hub_sent_at = models.DateTimeField(null=True, blank=True)
    hub_completed_at = models.DateTimeField(null=True, blank=True)

    # Failure handling
    retry_count = models.PositiveSmallIntegerField(default=0)
    failure_reason = models.TextField(blank=True)
    fallback_to_manual = models.BooleanField(default=False)

    priority = models.CharField(
        max_length=20,
        choices=[("stat", "STAT"), ("urgent", "Urgent"), ("routine", "Routine")],
        default="routine"
    )

    class Meta:
        db_table = "cymed_automation_queue"
        ordering = ["-priority", "created_at"]
        indexes = [
            models.Index(fields=["device", "status"]),
            models.Index(fields=["dispense_order_id", "status"]),
        ]
