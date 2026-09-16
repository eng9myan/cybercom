from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel

# Fee multiplier by trip type (one-way trips are a fraction of the full fare).
TRIP_MULTIPLIER = {
    "full_trip": Decimal("1.0"),
    "half_morning": Decimal("0.6"),
    "half_afternoon": Decimal("0.6"),
    "custom": Decimal("1.0"),
}


class TransportZone(BaseModel):
    name = models.CharField(max_length=100)  # e.g. "Zone 1"
    min_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    max_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # annual full-trip fare
    currency = models.CharField(max_length=10, default="AUD")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_transport_zones"
        ordering = ["min_km"]

    def __str__(self):
        return f"{self.name} ({self.min_km}-{self.max_km} km)"


class Bus(BaseModel):
    identifier = models.CharField(max_length=50)  # "Bus #12"
    rego = models.CharField(max_length=20, blank=True)
    make_model = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveSmallIntegerField(default=30)
    driver_name = models.CharField(max_length=255, blank=True)
    driver_license = models.CharField(max_length=50, blank=True)
    supervisor_name = models.CharField(max_length=255, blank=True)  # bus attendant
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_transport_buses"
        ordering = ["identifier"]

    @property
    def seats_taken(self) -> int:
        return self.subscriptions.filter(status="active").count()

    @property
    def seats_available(self) -> int:
        return max(0, self.capacity - self.seats_taken)

    def __str__(self):
        return self.identifier


class TransportSubscription(BaseModel):
    TRIP_CHOICES = [
        ("full_trip", "Full Trip (Two-Way)"),
        ("half_morning", "Half Trip — Morning"),
        ("half_afternoon", "Half Trip — Afternoon"),
        ("custom", "Custom / Multi-Address"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey("cyed_sis.Student", on_delete=models.CASCADE, related_name="transport_subscriptions")
    zone = models.ForeignKey(TransportZone, on_delete=models.PROTECT, related_name="subscriptions")
    trip_type = models.CharField(max_length=20, choices=TRIP_CHOICES, default="full_trip")
    pickup_address = models.CharField(max_length=500, blank=True)
    dropoff_address = models.CharField(max_length=500, blank=True)
    assigned_bus = models.ForeignKey(
        Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name="subscriptions"
    )
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    start_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_transport_subscriptions"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "student"], name="uniq_transport_sub_per_student")
        ]

    def compute_fee(self) -> Decimal:
        mult = TRIP_MULTIPLIER.get(self.trip_type, Decimal("1.0"))
        return (Decimal(self.zone.base_fee) * mult).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.student_id} · {self.trip_type} · {self.fee_amount}"


class CustomStop(BaseModel):
    """Per-weekday pickup/drop-off for shared-custody / multi-address arrangements."""

    WEEKDAYS = [("mon", "Monday"), ("tue", "Tuesday"), ("wed", "Wednesday"),
                ("thu", "Thursday"), ("fri", "Friday")]

    subscription = models.ForeignKey(TransportSubscription, on_delete=models.CASCADE, related_name="custom_stops")
    weekday = models.CharField(max_length=3, choices=WEEKDAYS)
    pickup_address = models.CharField(max_length=500, blank=True)
    dropoff_address = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cyed_transport_custom_stops"
        ordering = ["weekday"]
        constraints = [
            models.UniqueConstraint(fields=["subscription", "weekday"], name="uniq_custom_stop_per_weekday")
        ]

    def __str__(self):
        return f"{self.subscription_id} · {self.weekday}"


class BusRoute(BaseModel):
    name = models.CharField(max_length=150)
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name="routes")
    total_distance_km = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_transport_routes"
        ordering = ["name"]

    def __str__(self):
        return self.name


class RouteStop(BaseModel):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name="stops")
    sequence = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="route_stops"
    )

    class Meta:
        db_table = "cyed_transport_route_stops"
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.route_id} #{self.sequence} {self.name}"


class BusLocation(BaseModel):
    """
    Live GPS telemetry posted by the on-bus device (the device is the seam;
    this stores + serves the pings for the parent live map + ETA maths).
    """

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="locations")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    speed_kmh = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    heading = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    recorded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_transport_bus_locations"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant_id", "bus", "-created_at"])]

    def __str__(self):
        return f"{self.bus_id} @ ({self.lat},{self.lng})"


class RfidBoardingEvent(BaseModel):
    """
    A student tapping on/off the bus (RFID/scan). The physical reader posts these
    events; on creation a signal notifies the guardians ("child safely boarded").
    """

    EVENT_TYPES = [("board", "Boarded"), ("alight", "Alighted")]

    student = models.ForeignKey("cyed_sis.Student", on_delete=models.CASCADE, related_name="boarding_events")
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name="boarding_events")
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, default="board")
    occurred_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_transport_boarding_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student_id} {self.event_type} {self.bus_id}"
