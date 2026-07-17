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

    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name="orders")
    order_number = models.CharField(max_length=100)
    customer = models.ForeignKey(
        Partner, on_delete=models.PROTECT, related_name="pos_orders", null=True, blank=True
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
