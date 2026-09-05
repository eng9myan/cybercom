"""
Outbound logistics & distribution — the pack / dispatch / deliver domain that
sits between a sales order and the customer's dock.

    Shipment            one consolidated movement (origin -> destination), may
                        carry many customers' DeliveryOrders
    DeliveryOrder       one customer's goods within a shipment; weight / package
                        totals roll up from its Packages
    Package             a physical carton / pallet / crate — net + tare + gross
                        weight, dimensions, volumetric weight
    PackageItem         a SKU line inside a package
    Route               a driver's run for a day (last-mile / line-haul)
    RouteStop           an ordered stop on a route (pickup / delivery / hub)
    DeliveryEvent       tracking milestones, proof of delivery, exceptions

`services.recompute_*` rebuilds the rolled-up totals.
"""
from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel

Z2 = Decimal("0.01")
Z3 = Decimal("0.001")


class Carrier(BaseModel):
    MODES = [("road", "Road"), ("air", "Air"), ("sea", "Sea"), ("rail", "Rail"), ("courier", "Courier")]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    mode = models.CharField(max_length=10, choices=MODES, default="road")
    scac = models.CharField(max_length=20, blank=True)
    is_own_fleet = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_logistics_carriers"
        unique_together = [("tenant_id", "code")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Shipment(BaseModel):
    STATUS = [
        ("planning", "Planning"),
        ("booked", "Booked"),
        ("in_transit", "In Transit"),
        ("customs", "Customs Clearance"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("exception", "Exception"),
        ("cancelled", "Cancelled"),
    ]
    INCOTERMS = [
        ("EXW", "Ex Works"), ("FCA", "Free Carrier"), ("FOB", "Free On Board"),
        ("CIF", "Cost, Insurance & Freight"), ("CPT", "Carriage Paid To"),
        ("DAP", "Delivered At Place"), ("DDP", "Delivered Duty Paid"),
    ]

    number = models.CharField(max_length=100)
    carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT, null=True, blank=True,
                                related_name="shipments")
    mode = models.CharField(max_length=10, choices=Carrier.MODES, default="road")
    incoterm = models.CharField(max_length=3, choices=INCOTERMS, default="DAP")
    status = models.CharField(max_length=20, choices=STATUS, default="planning")

    origin_name = models.CharField(max_length=255)
    origin_country = models.CharField(max_length=2, default="JO")
    destination_name = models.CharField(max_length=255)
    destination_country = models.CharField(max_length=2, default="JO")

    planned_pickup = models.DateTimeField(null=True, blank=True)
    planned_delivery = models.DateTimeField(null=True, blank=True)
    actual_pickup = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)

    total_net_weight_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_gross_weight_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_volume_m3 = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_packages = models.PositiveIntegerField(default=0)
    total_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    freight_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_logistics_shipments"
        unique_together = [("tenant_id", "number")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} ({self.origin_country}->{self.destination_country}, {self.status})"


class DeliveryOrder(BaseModel):
    STATUS = [
        ("draft", "Draft"),
        ("allocated", "Allocated"),
        ("picking", "Picking"),
        ("packed", "Packed"),
        ("dispatched", "Dispatched"),
        ("in_transit", "In Transit"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("failed", "Delivery Failed"),
        ("returned", "Returned"),
    ]
    SERVICE_LEVELS = [("standard", "Standard"), ("express", "Express"), ("same_day", "Same Day")]

    number = models.CharField(max_length=100)
    shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="delivery_orders")
    sales_order_number = models.CharField(max_length=100, blank=True)
    customer_name = models.CharField(max_length=255)
    customer_reference = models.CharField(max_length=100, blank=True)
    destination_city = models.CharField(max_length=120, blank=True)
    destination_country = models.CharField(max_length=2, default="JO")

    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    service_level = models.CharField(max_length=12, choices=SERVICE_LEVELS, default="standard")
    promised_date = models.DateField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    net_weight_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    gross_weight_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    volume_m3 = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    package_count = models.PositiveIntegerField(default=0)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        db_table = "cycom_logistics_delivery_orders"
        unique_together = [("tenant_id", "number")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} — {self.customer_name} ({self.status})"

    @property
    def on_time(self):
        if not (self.delivered_at and self.promised_date):
            return None
        return self.delivered_at.date() <= self.promised_date


class Package(BaseModel):
    PACKAGING = [("carton", "Carton"), ("pallet", "Pallet"), ("crate", "Crate"),
                 ("envelope", "Envelope"), ("bag", "Bag"), ("drum", "Drum")]

    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name="packages")
    package_no = models.CharField(max_length=50)
    packaging_type = models.CharField(max_length=12, choices=PACKAGING, default="carton")

    net_weight_kg = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    tare_weight_kg = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    gross_weight_kg = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    length_cm = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    width_cm = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    height_cm = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    contents_description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_logistics_packages"
        unique_together = [("delivery_order", "package_no")]
        ordering = ["package_no"]

    @property
    def volume_m3(self) -> Decimal:
        return ((self.length_cm * self.width_cm * self.height_cm) / Decimal("1000000")).quantize(Decimal("0.0001"))

    @property
    def volumetric_weight_kg(self) -> Decimal:
        # IATA / courier dim-weight divisor 5000 (cm/kg)
        return ((self.length_cm * self.width_cm * self.height_cm) / Decimal("5000")).quantize(Z3)

    def recompute_gross(self, save=True):
        self.gross_weight_kg = (Decimal(self.net_weight_kg) + Decimal(self.tare_weight_kg)).quantize(Z3)
        if save:
            self.save(update_fields=["gross_weight_kg", "updated_at"])

    def __str__(self):
        return f"{self.delivery_order.number}/{self.package_no}"


class PackageItem(BaseModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="items")
    sku = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit_net_weight_kg = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        db_table = "cycom_logistics_package_items"
        ordering = ["id"]

    @property
    def line_net_weight_kg(self) -> Decimal:
        return (self.quantity * self.unit_net_weight_kg).quantize(Z3)


class Route(BaseModel):
    STATUS = [("planned", "Planned"), ("in_progress", "In Progress"),
              ("completed", "Completed"), ("aborted", "Aborted")]

    date = models.DateField()
    name = models.CharField(max_length=120)
    driver_name = models.CharField(max_length=255)
    vehicle_label = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="planned")

    planned_distance_km = models.DecimalField(max_digits=9, decimal_places=1, default=0)
    actual_distance_km = models.DecimalField(max_digits=9, decimal_places=1, default=0)
    planned_stops = models.PositiveIntegerField(default=0)
    completed_stops = models.PositiveIntegerField(default=0)
    failed_stops = models.PositiveIntegerField(default=0)
    load_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vehicle_capacity_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_logistics_routes"
        unique_together = [("tenant_id", "date", "name")]
        ordering = ["-date", "name"]

    @property
    def load_factor(self):
        if not self.vehicle_capacity_kg:
            return None
        return float(self.load_weight_kg) / float(self.vehicle_capacity_kg)

    def __str__(self):
        return f"{self.name} @ {self.date} ({self.driver_name})"


class RouteStop(BaseModel):
    STOP_TYPES = [("pickup", "Pickup"), ("delivery", "Delivery"), ("hub", "Hub / Depot")]
    STATUS = [("pending", "Pending"), ("arrived", "Arrived"), ("completed", "Completed"),
              ("failed", "Failed"), ("skipped", "Skipped")]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="stops")
    sequence = models.PositiveIntegerField()
    stop_type = models.CharField(max_length=10, choices=STOP_TYPES, default="delivery")
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name="route_stops")
    address = models.CharField(max_length=255, blank=True)
    planned_eta = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    dwell_minutes = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    distance_from_prev_km = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")

    class Meta:
        db_table = "cycom_logistics_route_stops"
        unique_together = [("route", "sequence")]
        ordering = ["route", "sequence"]


class DeliveryEvent(BaseModel):
    EVENT_TYPES = [
        ("created", "Order Created"),
        ("picked_up", "Picked Up"),
        ("arrived_hub", "Arrived at Hub"),
        ("departed_hub", "Departed Hub"),
        ("customs_hold", "Customs Hold"),
        ("customs_cleared", "Customs Cleared"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("attempt_failed", "Delivery Attempt Failed"),
        ("exception", "Exception"),
        ("returned", "Returned to Sender"),
    ]

    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    occurred_at = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    pod_name = models.CharField(max_length=255, blank=True)
    pod_reference = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "cycom_logistics_delivery_events"
        ordering = ["delivery_order", "occurred_at"]

    def __str__(self):
        return f"{self.delivery_order_id} {self.event_type} @ {self.occurred_at}"
