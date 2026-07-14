import uuid

from django.core.exceptions import ValidationError
from django.db import models


class NetworkStatus(models.TextChoices):
    """CyberCom master spec section 11 — exact status list. Default is
    standalone_only: subscribing to CyDrive must never silently publish a
    company to the CyMart delivery network (critical test case 7)."""

    STANDALONE_ONLY = "standalone_only", "Standalone Only"
    NETWORK_APPLICATION_PENDING = "network_application_pending", "Network Application Pending"
    NETWORK_APPROVED = "network_approved", "Network Approved"
    NETWORK_ACTIVE = "network_active", "Network Active"
    NETWORK_SUSPENDED = "network_suspended", "Network Suspended"
    NETWORK_TERMINATED = "network_terminated", "Network Terminated"


class DeliveryCompany(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    service_areas = models.JSONField(default=list, blank=True)

    # CyDrive SaaS subscription — entirely independent of CyMart network
    # membership. Critical test case 8: suspending network_status must
    # never touch this.
    cydrive_subscription_active = models.BooleanField(default=True)

    network_status = models.CharField(
        max_length=32, choices=NetworkStatus.choices, default=NetworkStatus.STANDALONE_ONLY
    )
    network_joined_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cydrive_delivery_company"

    def __str__(self):
        return self.name

    @property
    def is_network_eligible_for_jobs(self) -> bool:
        return self.network_status == NetworkStatus.NETWORK_ACTIVE

    def apply_to_network(self):
        if self.network_status != NetworkStatus.STANDALONE_ONLY:
            raise ValidationError(
                f"Cannot apply to network from status '{self.network_status}'."
            )
        self.network_status = NetworkStatus.NETWORK_APPLICATION_PENDING
        self.save(update_fields=["network_status", "updated_at"])

    def approve_network_membership(self):
        if self.network_status != NetworkStatus.NETWORK_APPLICATION_PENDING:
            raise ValidationError(
                f"Cannot approve from status '{self.network_status}'."
            )
        self.network_status = NetworkStatus.NETWORK_APPROVED
        self.save(update_fields=["network_status", "updated_at"])

    def activate_network_membership(self):
        if self.network_status != NetworkStatus.NETWORK_APPROVED:
            raise ValidationError(
                f"Cannot activate from status '{self.network_status}'."
            )
        from django.utils import timezone

        self.network_status = NetworkStatus.NETWORK_ACTIVE
        self.network_joined_at = timezone.now()
        self.save(update_fields=["network_status", "network_joined_at", "updated_at"])

    def suspend_network_membership(self):
        if self.network_status != NetworkStatus.NETWORK_ACTIVE:
            raise ValidationError(
                f"Cannot suspend from status '{self.network_status}'."
            )
        self.network_status = NetworkStatus.NETWORK_SUSPENDED
        self.save(update_fields=["network_status", "updated_at"])
        # Explicitly does NOT touch cydrive_subscription_active — the two
        # are independent by design (critical test case 8).


class VehicleType(models.TextChoices):
    MOTORCYCLE = "motorcycle", "Motorcycle"
    CAR = "car", "Car"
    VAN = "van", "Van"
    REFRIGERATED_VAN = "refrigerated_van", "Refrigerated Van"
    TRUCK = "truck", "Truck"


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(DeliveryCompany, on_delete=models.CASCADE, related_name="vehicles")
    vehicle_type = models.CharField(max_length=32, choices=VehicleType.choices)
    plate_number = models.CharField(max_length=32)
    capacity_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_temperature_controlled = models.BooleanField(default=False)
    insurance_expiry = models.DateField(null=True, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cydrive_vehicle"
        constraints = [
            models.UniqueConstraint(fields=["company", "plate_number"], name="unique_plate_per_company")
        ]

    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_type})"

    @property
    def is_compliant(self) -> bool:
        from django.utils import timezone

        today = timezone.now().date()
        if self.insurance_expiry and self.insurance_expiry < today:
            return False
        if self.license_expiry and self.license_expiry < today:
            return False
        return True


class DriverStatus(models.TextChoices):
    OFF_SHIFT = "off_shift", "Off Shift"
    AVAILABLE = "available", "Available"
    ON_JOB = "on_job", "On Job"
    SUSPENDED = "suspended", "Suspended"


class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(DeliveryCompany, on_delete=models.CASCADE, related_name="drivers")
    user_id = models.UUIDField(db_index=True, help_text="CyIdentity user id for this driver.")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    license_number = models.CharField(max_length=64)
    license_expiry = models.DateField(null=True, blank=True)
    zone = models.CharField(max_length=100, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    status = models.CharField(max_length=16, choices=DriverStatus.choices, default=DriverStatus.OFF_SHIFT)
    current_vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="current_drivers"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cydrive_driver"
        constraints = [
            models.UniqueConstraint(fields=["company", "user_id"], name="unique_driver_user_per_company")
        ]

    def __str__(self):
        return self.name

    @property
    def is_eligible_for_dispatch(self) -> bool:
        return self.status == DriverStatus.AVAILABLE


class DeliveryJobStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ASSIGNED = "assigned", "Assigned"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    PICKED_UP = "picked_up", "Picked Up"
    IN_TRANSIT = "in_transit", "In Transit"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    RETURNED = "returned", "Returned"
    CANCELLED = "cancelled", "Cancelled"


class DeliveryJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(DeliveryCompany, on_delete=models.CASCADE, related_name="jobs")
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs"
    )

    # Soft reference — CyDrive is standalone-capable (master spec section
    # 11), so a job doesn't have to come from CyMart at all. When it does,
    # this links back to the CyMart MarketplaceOrder without a real FK
    # (separate service, separate database).
    source_order_id = models.UUIDField(null=True, blank=True, db_index=True)

    pickup_address = models.JSONField(default=dict)
    dropoff_address = models.JSONField(default=dict)
    requires_temperature_control = models.BooleanField(default=False)
    package_size = models.CharField(max_length=32, blank=True)

    status = models.CharField(
        max_length=16, choices=DeliveryJobStatus.choices, default=DeliveryJobStatus.PENDING
    )
    cash_collection_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_collected = models.BooleanField(default=False)

    proof_of_delivery = models.JSONField(default=dict, blank=True)
    failure_reason = models.CharField(max_length=300, blank=True)

    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cydrive_delivery_job"
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["driver", "status"]),
        ]

    def __str__(self):
        return f"DeliveryJob({self.id}, {self.status})"
