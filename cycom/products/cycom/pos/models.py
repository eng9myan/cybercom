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

    @property
    def discount_amount(self):
        """Total currency value discounted off this order's lines (gross list
        price minus the discounted subtotal). This is the figure the
        `pos_discount` approval matrix bands against — see access.approvals."""
        total = Decimal("0")
        for line in self.lines.all():
            gross = (line.quantity * line.unit_price).quantize(Decimal("0.01"))
            total += gross - line.subtotal
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
    # quantity doubles as a weight (e.g. kg) when product.pricing_mode=="weight"
    # — same decimal field, no schema change needed for that vertical.
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Required at checkout when product.tracking_mode=="serial" — exactly
    # `quantity` serials, passed through to the issuing StockMove (see
    # pos.services.checkout_order / inventory.services.apply_stock_move).
    serial_numbers = models.JSONField(default=list, blank=True)

    # Captured at checkout (not settable directly) so a later return restocks
    # at the ORIGINAL cost/lot, not whatever the average/lot has drifted to
    # since — see pos.services.checkout_order and post_return.
    unit_cost_at_sale = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    lot_number_at_sale = models.CharField(max_length=100, blank=True)

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

    @property
    def returned_quantity(self):
        """Sum of quantity already returned against this line across every
        non-rejected return (draft/pending_approval hold the qty too, so two
        concurrent partial-return requests can't both over-return)."""
        return sum(
            (rl.quantity for rl in self.return_lines.exclude(ret__status="rejected")),
            Decimal("0"),
        )


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


class PosReturn(BaseModel):
    """A return/refund against one paid POSOrder — full or partial (line-
    level, via PosReturnLine). Value-based-approval-gated (pos_refund policy,
    same engine as pos_discount) with an at-terminal manager-PIN/barcode
    fallback — see pos.services and access.credentials."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_approval", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    order = models.ForeignKey(POSOrder, on_delete=models.PROTECT, related_name="returns")
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    requested_by = models.CharField(max_length=255, blank=True)
    # Set to whoever's authority actually cleared it — the caller's own
    # identity for a self-service approval, or the credential-verified
    # manager's user_id for a PIN/barcode approval (see pos.views).
    approved_by_user_id = models.CharField(max_length=255, blank=True)
    approval_method = models.CharField(
        max_length=10, blank=True,
        choices=[("self", "Self (own role)"), ("pin", "Manager PIN"), ("barcode", "Manager Barcode")],
    )
    rejection_reason = models.TextField(blank=True)
    amount_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_pos_returns"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Return {self.id} for {self.order.order_number} ({self.status})"


class PosReturnLine(BaseModel):
    ret = models.ForeignKey(PosReturn, on_delete=models.CASCADE, related_name="lines")
    order_line = models.ForeignKey(POSOrderLine, on_delete=models.PROTECT, related_name="return_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    restock = models.BooleanField(default=True)
    # Which specific units are going back to stock, for a serial-tracked
    # product — must be a subset of order_line.serial_numbers, length == quantity.
    serial_numbers = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "cycom_pos_return_lines"
        ordering = ["id"]

    @property
    def refund_amount(self):
        line = self.order_line
        if not line.quantity:
            return Decimal("0")
        proportion = self.quantity / line.quantity
        return (line.subtotal * proportion).quantize(Decimal("0.01"))

    @property
    def refund_tax(self):
        line = self.order_line
        if not line.quantity:
            return Decimal("0")
        proportion = self.quantity / line.quantity
        return (line.tax_amount * proportion).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.quantity} x {self.order_line.product} (return {self.ret_id})"
