import uuid

from django.db import models

from products.cymart.orders.models import MarketplaceOrder


class DeliveryZone(models.Model):
    """A servable area for launch — a city centered on a point with a
    radius, not a full polygon (that's a later precision upgrade once
    there's real map-provider integration). ZoneService checks
    deliverability against this with plain haversine distance, no
    external maps API required to run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    center_lat = models.DecimalField(max_digits=9, decimal_places=6)
    center_lng = models.DecimalField(max_digits=9, decimal_places=6)
    radius_km = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_delivery_zone"

    def __str__(self):
        return f"{self.name} ({self.city}, {self.radius_km}km)"


class VehicleType(models.TextChoices):
    BIKE = "bike", "Bike"
    MOTORCYCLE = "motorcycle", "Motorcycle"
    CAR = "car", "Car"


class Driver(models.Model):
    """A 3PL/gig courier — launch runs on partner couriers, not an owned
    fleet, but the assignment model is the same either way."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32)
    vehicle_type = models.CharField(max_length=12, choices=VehicleType.choices, default=VehicleType.MOTORCYCLE)

    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_active = models.BooleanField(default=True)  # employable / not deactivated
    is_online = models.BooleanField(default=False)  # currently on shift, eligible for dispatch

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_driver"

    def __str__(self):
        return self.name


class DeliveryRunStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class DeliveryRun(models.Model):
    """One driver trip that can carry more than one order — e.g. a
    customer's food order and grocery order batched into a single trip
    with one driver making two pickups and one drop-off. Each order still
    gets its own DeliveryAssignment (and its own customer-facing tracking
    timeline via TrackingEvent); this just groups them under one
    driver/trip so dispatch only sends one courier out, not two."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="runs")
    customer_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=12, choices=DeliveryRunStatus.choices, default=DeliveryRunStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymart_delivery_run"

    def __str__(self):
        return f"DeliveryRun({self.id}, driver={self.driver_id}, {self.status})"


class AssignmentStatus(models.TextChoices):
    ASSIGNED = "assigned", "Assigned"
    PICKED_UP = "picked_up", "Picked up"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class DeliveryAssignment(models.Model):
    """One order has at most one *active* assignment — a cancelled one can
    be replaced by a fresh dispatch, but never two live assignments for
    the same order. Optionally belongs to a DeliveryRun when it was
    dispatched together with the customer's other order(s)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        MarketplaceOrder, on_delete=models.CASCADE, related_name="delivery_assignment"
    )
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="assignments")
    run = models.ForeignKey(
        DeliveryRun, on_delete=models.CASCADE, related_name="assignments", null=True, blank=True
    )
    # Pickup order within the run — 0 = first stop. Meaningless when run
    # is null (a lone, unbatched assignment).
    stop_order = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(
        max_length=12, choices=AssignmentStatus.choices, default=AssignmentStatus.ASSIGNED
    )

    assigned_at = models.DateTimeField(auto_now_add=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymart_delivery_assignment"

    def __str__(self):
        return f"DeliveryAssignment(order={self.order_id}, {self.status})"


class TrackingEvent(models.Model):
    """The live-tracking timeline a customer sees for their order —
    'placed → accepted → preparing → picked up → arriving'."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        DeliveryAssignment, on_delete=models.CASCADE, related_name="events"
    )
    status = models.CharField(max_length=12, choices=AssignmentStatus.choices)
    note = models.CharField(max_length=200, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_tracking_event"
        ordering = ["occurred_at"]

    def __str__(self):
        return f"TrackingEvent({self.status}, {self.occurred_at})"
