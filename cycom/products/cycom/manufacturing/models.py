from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account
from products.cycom.company.models import Company
from products.cycom.inventory.models import Product, Warehouse


class BillOfMaterial(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="boms")
    name = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=14, decimal_places=4, default=1,
        help_text="How many units of `product` this BoM produces per run.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_manufacturing_boms"
        ordering = ["product__internal_ref", "name"]

    def __str__(self):
        return f"{self.name} ({self.product.sku})"


class BOMComponent(BaseModel):
    bom = models.ForeignKey(BillOfMaterial, on_delete=models.CASCADE, related_name="components")
    component = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="used_in_boms")
    quantity = models.DecimalField(
        max_digits=14, decimal_places=4,
        help_text="Quantity of `component` needed per one BoM run (see BillOfMaterial.quantity).",
    )

    class Meta:
        db_table = "cycom_manufacturing_bom_components"

    def __str__(self):
        return f"{self.component.sku} x{self.quantity}"


class WorkCenter(BaseModel):
    """A machine, cell, or station that runs routing operations — the unit
    capacity planning measures load against."""

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    capacity_per_day_hours = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_manufacturing_work_centers"
        unique_together = [("tenant_id", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Routing(BaseModel):
    """The sequence of operations needed to build one product. A
    ManufacturingOrder without a routing for its product keeps the old
    instant-complete behavior — routings are opt-in, not a breaking change."""

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="routings")
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_manufacturing_routings"
        ordering = ["product__internal_ref", "name"]

    def __str__(self):
        return f"{self.name} ({self.product.sku})"


class RoutingOperation(BaseModel):
    routing = models.ForeignKey(Routing, on_delete=models.CASCADE, related_name="operations")
    sequence = models.PositiveIntegerField(default=10)
    work_center = models.ForeignKey(
        WorkCenter, on_delete=models.PROTECT, related_name="routing_operations"
    )
    name = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField(
        help_text="Minutes to run this operation for one full BoM batch."
    )

    class Meta:
        db_table = "cycom_manufacturing_routing_operations"
        ordering = ["sequence", "id"]

    def __str__(self):
        return f"{self.routing} — {self.name}"


class ManufacturingOrder(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    bom = models.ForeignKey(BillOfMaterial, on_delete=models.PROTECT, related_name="orders")
    # Auto-resolved on create from bom.product's active Routing, if any.
    routing = models.ForeignKey(
        Routing, on_delete=models.SET_NULL, null=True, blank=True, related_name="manufacturing_orders"
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="manufacturing_orders")
    wip_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="+",
        help_text="Work-in-progress clearing account — debited on component consumption, credited on finished-goods receipt.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    scheduled_date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, null=True, blank=True, related_name="manufacturing_orders"
    )

    class Meta:
        db_table = "cycom_manufacturing_orders"
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"MO {self.id} — {self.bom.product.sku} x{self.quantity} ({self.status})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new and not self.routing_id:
            self.routing = (
                Routing.objects.filter(tenant_id=self.tenant_id, product=self.bom.product, is_active=True)
                .first()
            )
        super().save(*args, **kwargs)
        if is_new and self.routing_id and not self.work_orders.exists():
            operations = list(self.routing.operations.select_related("work_center").all())
            for i, op in enumerate(operations):
                WorkOrder.objects.create(
                    tenant_id=self.tenant_id,
                    manufacturing_order=self,
                    routing_operation=op,
                    work_center=op.work_center,
                    sequence=op.sequence,
                    planned_duration_minutes=op.duration_minutes,
                    status="ready" if i == 0 else "pending",
                )


class WorkOrder(BaseModel):
    """One routing operation's execution against a specific
    ManufacturingOrder. Strictly sequenced: only one work order per MO is
    ever 'ready' at a time — finishing one is what makes the next ready."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("ready", "Ready"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    manufacturing_order = models.ForeignKey(
        ManufacturingOrder, on_delete=models.CASCADE, related_name="work_orders"
    )
    routing_operation = models.ForeignKey(
        RoutingOperation, on_delete=models.PROTECT, related_name="work_orders"
    )
    # Denormalized from routing_operation.work_center at creation — protects
    # this record's history if the routing is edited later.
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, related_name="work_orders")
    sequence = models.PositiveIntegerField()
    planned_duration_minutes = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_manufacturing_work_orders"
        ordering = ["manufacturing_order", "sequence"]

    def __str__(self):
        return f"{self.manufacturing_order} — {self.routing_operation.name} ({self.status})"

    @property
    def actual_duration_minutes(self):
        if self.started_at and self.finished_at:
            return round((self.finished_at - self.started_at).total_seconds() / 60, 1)
        return None
