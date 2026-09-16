from decimal import Decimal

from django.db import models
from django.db.models import F, Sum

from platform.common.models import BaseModel


class Supplier(BaseModel):
    name = models.CharField(max_length=255)
    abn = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_suppliers"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseRequest(BaseModel):
    """
    A request to buy something, raised by any staff member and routed through
    approval before it can become a purchase order. Multi-step: a request over
    `HIGH_VALUE_THRESHOLD` needs a second (leadership) approval.
    """

    STATUS = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved_l1", "Approved (finance)"),
        ("approved", "Fully Approved"),
        ("rejected", "Rejected"),
        ("converted", "Converted to PO"),
    ]
    HIGH_VALUE_THRESHOLD = Decimal("5000")

    reference = models.CharField(max_length=100, blank=True)
    requested_by = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=100, blank=True)
    justification = models.TextField(blank=True)
    needed_by = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    suggested_supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests"
    )
    purchase_order = models.ForeignKey(
        "PurchaseOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="source_requests"
    )

    class Meta:
        db_table = "cyed_purchase_requests"
        ordering = ["-created_at"]

    @property
    def estimated_total(self) -> Decimal:
        return self.lines.aggregate(t=Sum(F("quantity") * F("estimated_unit_price")))["t"] or Decimal("0")

    @property
    def needs_second_approval(self) -> bool:
        return self.estimated_total >= self.HIGH_VALUE_THRESHOLD

    def __str__(self):
        return f"PR {self.reference or self.id} ({self.status})"


class PurchaseRequestLine(BaseModel):
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    estimated_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    inventory_item = models.ForeignKey(
        "cyed_inventory.InventoryItem", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="request_lines",
    )

    class Meta:
        db_table = "cyed_purchase_request_lines"
        ordering = ["id"]

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.quantity) * Decimal(self.estimated_unit_price)

    def __str__(self):
        return f"{self.description} x{self.quantity}"


class ApprovalStep(BaseModel):
    """One decision in a request's approval chain. Append-only audit of who
    approved or rejected, when, and why."""

    DECISIONS = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]

    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name="approvals")
    level = models.PositiveSmallIntegerField(default=1)  # 1 = finance, 2 = leadership
    approver = models.CharField(max_length=255, blank=True)
    decision = models.CharField(max_length=20, choices=DECISIONS, default="pending")
    decided_at = models.DateTimeField(null=True, blank=True)
    comment = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cyed_purchase_approval_steps"
        ordering = ["level", "created_at"]

    def __str__(self):
        return f"L{self.level} {self.decision} by {self.approver}"


class PurchaseOrder(BaseModel):
    STATUS = [("draft", "Draft"), ("ordered", "Ordered"), ("partially_received", "Partially Received"),
              ("received", "Received"), ("cancelled", "Cancelled")]

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    order_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cyed_purchase_orders"
        ordering = ["-created_at"]

    @property
    def total(self) -> Decimal:
        return self.lines.aggregate(t=Sum(F("quantity") * F("unit_price")))["t"] or Decimal("0")

    def __str__(self):
        return f"PO {self.reference or self.id} ({self.status})"


class PurchaseOrderLine(BaseModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    inventory_item = models.ForeignKey(
        "cyed_inventory.InventoryItem", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="po_lines",
    )
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "cyed_purchase_order_lines"
        ordering = ["id"]

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.quantity) * Decimal(self.unit_price)

    @property
    def quantity_outstanding(self) -> Decimal:
        return Decimal(self.quantity) - Decimal(self.quantity_received)

    def __str__(self):
        return f"{self.description} x{self.quantity}"


class GoodsReceipt(BaseModel):
    """
    Goods physically received against a purchase order. Receiving a line moves
    stock into Inventory (StockMove) and posts the cost to Accounting.
    """

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="receipts")
    received_date = models.DateField(null=True, blank=True)
    received_by = models.CharField(max_length=255, blank=True)
    delivery_note = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=500, blank=True)
    journal_entry = models.ForeignKey(
        "cyed_finance.JournalEntry", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="goods_receipts",
    )

    class Meta:
        db_table = "cyed_goods_receipts"
        ordering = ["-created_at"]

    @property
    def total_value(self) -> Decimal:
        return sum((ln.line_value for ln in self.lines.all()), Decimal("0"))

    def __str__(self):
        return f"GRN {self.delivery_note or self.id}"


class GoodsReceiptLine(BaseModel):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    purchase_order_line = models.ForeignKey(
        PurchaseOrderLine, on_delete=models.CASCADE, related_name="receipt_lines"
    )
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_move = models.ForeignKey(
        "cyed_inventory.StockMove", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="receipt_lines",
    )

    class Meta:
        db_table = "cyed_goods_receipt_lines"
        ordering = ["id"]

    @property
    def line_value(self) -> Decimal:
        return Decimal(self.quantity_received) * Decimal(self.purchase_order_line.unit_price)

    def __str__(self):
        return f"received {self.quantity_received} of {self.purchase_order_line_id}"
