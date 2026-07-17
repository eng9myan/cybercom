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


class POSOrder(BaseModel):
    STATUS_CHOICES = [("draft", "Draft"), ("paid", "Paid"), ("void", "Void")]

    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name="orders")
    order_number = models.CharField(max_length=100)
    customer = models.ForeignKey(
        Partner, on_delete=models.PROTECT, related_name="pos_orders", null=True, blank=True
    )
    currency = models.CharField(max_length=10, default="JOD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="pos_orders_cash")
    revenue_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="pos_orders_revenue")
    tax_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="pos_orders_tax", null=True, blank=True
    )
    cogs_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="pos_orders_cogs")

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


class POSOrderLine(BaseModel):
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="pos_order_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_pos_order_lines"
        ordering = ["id"]

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_percent / 100).quantize(Decimal("0.01"))
