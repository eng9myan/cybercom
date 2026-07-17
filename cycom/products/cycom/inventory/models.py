from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account, JournalEntry


class Warehouse(BaseModel):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_inventory_warehouses"
        unique_together = [("tenant_id", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Product(BaseModel):
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    uom = models.CharField(max_length=20, default="each")
    inventory_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="products_as_inventory"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_inventory_products"
        unique_together = [("tenant_id", "sku")]
        ordering = ["sku"]

    def __str__(self):
        return f"{self.sku} — {self.name}"


class StockItem(BaseModel):
    """Valuation ledger balance: quantity + weighted-average cost per product/warehouse."""

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_items")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stock_items")
    quantity_on_hand = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    average_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        db_table = "cycom_inventory_stock_items"
        unique_together = [("tenant_id", "product", "warehouse")]

    @property
    def value(self):
        return self.quantity_on_hand * self.average_cost

    def __str__(self):
        return f"{self.product} @ {self.warehouse}: {self.quantity_on_hand}"


class StockMove(BaseModel):
    MOVE_TYPES = [
        ("receipt", "Receipt"),
        ("issue", "Issue"),
        ("transfer", "Transfer"),
        ("adjustment", "Adjustment"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_approval", "Pending Approval"),
        ("approved", "Approved"),
        ("done", "Done"),
        ("rejected", "Rejected"),
    ]

    move_type = models.CharField(max_length=20, choices=MOVE_TYPES)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="moves")
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="moves_out",
        help_text="Source warehouse (issue/transfer/adjustment) or destination (receipt).",
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="moves_in", null=True, blank=True
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # GL offset account for receipts (Cr, e.g. GRNI clearing) and issues
    # (Dr, e.g. COGS) — not needed for transfer/adjustment between two
    # inventory-account-holding sides.
    offset_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="stock_moves", null=True, blank=True
    )

    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_inventory_stock_moves"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.move_type} {self.product} x{self.quantity} ({self.status})"


class InternalOrder(BaseModel):
    """
    Branch replenishment request: submit -> allocate -> dispatch -> receive.
    Dispatch reuses the same StockMove/apply_stock_move machinery as any
    other transfer (see inventory/services.py) — this order's own
    allocate/dispatch steps ARE the approval gate, so the underlying
    StockMove is created pre-approved rather than requiring a second,
    redundant approval.
    """

    PRIORITY_CHOICES = [("low", "Low"), ("normal", "Normal"), ("urgent", "Urgent")]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("allocated", "Allocated"),
        ("dispatched", "Dispatched"),
        ("received", "Received"),
        ("partially_received", "Partially Received"),
        ("cancelled", "Cancelled"),
    ]

    number = models.CharField(max_length=100)
    source_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="internal_orders_out"
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="internal_orders_in"
    )
    required_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="normal")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_inventory_internal_orders"
        unique_together = [("tenant_id", "number")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} ({self.status})"


class InternalOrderLine(BaseModel):
    order = models.ForeignKey(InternalOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="internal_order_lines")
    requested_qty = models.DecimalField(max_digits=12, decimal_places=4)
    allocated_qty = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    shipped_qty = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    received_qty = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    discrepancy_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_inventory_internal_order_lines"
        ordering = ["id"]
