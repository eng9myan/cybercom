from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account, JournalEntry

# S-3: catalog.Product is now the single product master (see
# products/cycom/catalog/models.py) — inventory.Product is retired. Re-exported
# here so every existing `from products.cycom.inventory.models import Product`
# import (pos, sales, procurement, manufacturing, access, cyai_memory,
# simulations) keeps working unchanged; it's the same class either way, Django
# resolves FK targets by the class object, not the import path.
from products.cycom.catalog.models import Product  # noqa: F401


class Warehouse(BaseModel):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    # S-2: per-branch POS GL defaults. A multi-branch retailer configures
    # these once per warehouse/branch instead of a till clerk supplying
    # chart-of-accounts UUIDs on every sale (see pos.serializers.POSOrderSerializer,
    # which resolves an order's accounts from here when the request omits them).
    pos_cash_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="warehouses_pos_cash"
    )
    pos_revenue_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="warehouses_pos_revenue"
    )
    pos_cogs_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="warehouses_pos_cogs"
    )
    pos_tax_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="warehouses_pos_tax"
    )
    pos_advance_liability_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="warehouses_pos_advance_liability",
    )

    class Meta:
        db_table = "cycom_inventory_warehouses"
        unique_together = [("tenant_id", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


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


class StockLot(BaseModel):
    """One batch/lot of a `tracking_mode=batch` product at a warehouse — its
    own quantity + weighted-average cost, alongside (not instead of) the
    product/warehouse StockItem aggregate, which every move still updates the
    same way it always has. Issuing without an explicit lot picks FEFO
    (earliest `expiry_date` first, no-expiry lots last) across a product/
    warehouse's lots — see inventory.services.apply_stock_move."""

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="lots")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stock_lots")
    lot_number = models.CharField(max_length=100)
    expiry_date = models.DateField(null=True, blank=True)
    quantity_on_hand = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    average_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        db_table = "cycom_inventory_stock_lots"
        unique_together = [("tenant_id", "product", "warehouse", "lot_number")]
        ordering = ["expiry_date", "lot_number"]

    def __str__(self):
        return f"{self.product} lot {self.lot_number} @ {self.warehouse}: {self.quantity_on_hand}"


class SerialUnit(BaseModel):
    """One physically serialized unit of a `tracking_mode=serial` product.
    `sold_reference` is a loose string reference (e.g. a POS order number),
    not an FK — inventory doesn't depend on pos/sales, matching how
    StockMove.reference already works."""

    STATUS_CHOICES = [
        ("in_stock", "In Stock"),
        ("issued", "Issued"),
        ("returned", "Returned"),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="serial_units")
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name="serial_units",
        help_text="Null once issued — the unit has left the warehouse.",
    )
    serial_number = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_stock")
    sold_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cycom_inventory_serial_units"
        unique_together = [("tenant_id", "product", "serial_number")]
        ordering = ["serial_number"]

    def __str__(self):
        return f"{self.product} #{self.serial_number} ({self.status})"


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

    # Batch/lot tracking (tracking_mode="batch"): lot_number/expiry_date are
    # the receipt-time input; `lot` is set by apply_stock_move once resolved
    # (the specific StockLot a receipt created/topped up, or — for issue — the
    # lot actually consumed, explicit or FEFO-picked).
    lot = models.ForeignKey(
        StockLot, on_delete=models.PROTECT, null=True, blank=True, related_name="moves"
    )
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Serial tracking (tracking_mode="serial"): the serials this move
    # receives or issues — must number exactly `quantity`.
    serial_numbers = models.JSONField(default=list, blank=True)

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
