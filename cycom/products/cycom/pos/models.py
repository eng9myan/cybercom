from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account, JournalEntry
from products.cycom.ar_ap.models import Partner
from products.cycom.inventory.models import Product, Warehouse


class POSSession(BaseModel):
    STATUS_CHOICES = [("open", "Open"), ("closed", "Closed")]

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="pos_sessions")
    cashier = models.CharField(max_length=255, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    class Meta:
        db_table = "cycom_pos_sessions"
        ordering = ["-opened_at"]

    def __str__(self):
        return f"Session @ {self.warehouse} ({self.status})"


# Any line discount above this triggers the discount-exception approval gate.
DISCOUNT_APPROVAL_THRESHOLD_PERCENT = Decimal("10")


class POSOrder(BaseModel):
    STATUS_CHOICES = [("draft", "Draft"), ("paid", "Paid"), ("void", "Void")]
    DISCOUNT_APPROVAL_CHOICES = [
        ("not_required", "Not Required"),
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    ORDER_TYPE_CHOICES = [("sale", "Sale"), ("layaway", "Layaway / Advance")]

    # ── Ported from CyShop: restaurant / kitchen-display (KDS) fields ────────
    # These drive the KDS terminal (see pos.Device type "KDS"): tickets flow
    # PENDING -> IN_PROGRESS -> READY -> SERVED on the kitchen screen, keyed off
    # `kitchen_status`, while `source`/`table_ref`/walk-in customer capture the
    # front-of-house context an accounting-only POSOrder didn't carry.
    SOURCE_CHOICES = [
        ("POS", "POS Terminal"),
        ("KIOSK", "Self-Service Kiosk"),
        ("ONLINE", "Online Order"),
    ]
    KITCHEN_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("ready", "Ready"),
        ("served", "Served"),
    ]

    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name="orders")
    order_number = models.CharField(max_length=100)
    customer = models.ForeignKey(
        Partner, on_delete=models.PROTECT, related_name="pos_orders", null=True, blank=True
    )
    # Walk-in / front-of-house capture (no Partner record required).
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=50, blank=True)
    table_ref = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="POS")
    kitchen_status = models.CharField(
        max_length=20, choices=KITCHEN_STATUS_CHOICES, default="pending", db_index=True
    )
    currency = models.CharField(max_length=10, default="JOD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default="sale")
    discount_approval_status = models.CharField(
        max_length=20, choices=DISCOUNT_APPROVAL_CHOICES, default="not_required"
    )
    discount_approved_by = models.CharField(max_length=255, blank=True)
    discount_rejection_reason = models.TextField(blank=True)

    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="pos_orders_cash")
    revenue_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="pos_orders_revenue")
    tax_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="pos_orders_tax", null=True, blank=True
    )
    cogs_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="pos_orders_cogs")
    # Customer-deposits liability account — required for layaway orders only.
    # Each advance payment books Dr Cash / Cr this account (no revenue yet,
    # since goods haven't been released); checkout reverses the accumulated
    # balance into revenue/tax the same moment stock is issued.
    advance_liability_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="pos_orders_advance_liability", null=True, blank=True
    )

    amount_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_pos_orders"
        unique_together = [("tenant_id", "order_number")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} ({self.status})"

    @property
    def amount_paid(self):
        total = Decimal("0")
        for p in self.payments.all():
            total += p.amount
        return total

    # Ordered kitchen-ticket flow; advance_kitchen() steps one stage forward.
    KITCHEN_FLOW = ["pending", "in_progress", "ready", "served"]

    def advance_kitchen(self):
        """Move the kitchen ticket one stage forward; no-op once served."""
        idx = self.KITCHEN_FLOW.index(self.kitchen_status)
        if idx < len(self.KITCHEN_FLOW) - 1:
            self.kitchen_status = self.KITCHEN_FLOW[idx + 1]
            self.save(update_fields=["kitchen_status", "updated_at"])
        return self.kitchen_status


class POSOrderPayment(BaseModel):
    """A single advance/deposit payment against a layaway order."""

    METHOD_CHOICES = [("cash", "Cash"), ("card", "Card"), ("transfer", "Bank Transfer")]

    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="cash")
    paid_at = models.DateTimeField(auto_now_add=True)
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_pos_order_payments"
        ordering = ["paid_at"]

    def __str__(self):
        return f"{self.order.order_number} advance {self.amount}"


class POSOrderLine(BaseModel):
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="pos_order_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_pos_order_lines"
        ordering = ["id"]

    @property
    def subtotal(self):
        gross = self.quantity * self.unit_price
        if self.discount_percent:
            gross = gross * (Decimal("100") - self.discount_percent) / Decimal("100")
        return gross.quantize(Decimal("0.01"))

    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_percent / 100).quantize(Decimal("0.01"))


# ── Ported from CyShop ──────────────────────────────────────────────────────
# Device + PosReceipt bring the retail/restaurant terminal layer Cycom lacked.
# CyShop scoped a Device to Company+Branch; Cycom has no per-tenant Company, so
# a Device is optionally tied to an inventory Warehouse (its physical location)
# and otherwise scoped by tenant_id.


class Device(BaseModel):
    """
    A registered fullscreen terminal at a location (POS terminal, kitchen
    display, waiter handheld, customer-facing display, warehouse scanner,
    self-order kiosk). Each device_type maps to a standalone frontend route
    outside the manager shell.
    """

    DEVICE_TYPES = [
        ("POS", "POS Terminal"),
        ("KDS", "Kitchen Display"),
        ("WAITER", "Waiter Handheld"),
        ("CUSTOMER_DISPLAY", "Customer-Facing Display"),
        ("WAREHOUSE_SCANNER", "Warehouse Scanner"),
        ("SELF_ORDER", "Self-Order Kiosk"),
    ]
    ROUTE_BY_TYPE = {
        "POS": "/pos-terminal",
        "KDS": "/kds",
        "WAITER": "/waiter",
        "CUSTOMER_DISPLAY": "/customer-display",
        "WAREHOUSE_SCANNER": "/warehouse-scanner",
        "SELF_ORDER": "/self-order",
    }

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="devices", null=True, blank=True
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_pos_devices"
        ordering = ["warehouse", "device_type", "name"]
        unique_together = [("tenant_id", "code")]

    @property
    def route(self):
        return self.ROUTE_BY_TYPE.get(self.device_type, "/")

    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"


class PosReceipt(BaseModel):
    order = models.OneToOneField(POSOrder, on_delete=models.PROTECT, related_name="receipt")
    receipt_number = models.CharField(max_length=50, db_index=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    emailed_at = models.DateTimeField(null=True, blank=True)
    qr_data = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_pos_receipts"
        unique_together = [("tenant_id", "receipt_number")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.receipt_number
