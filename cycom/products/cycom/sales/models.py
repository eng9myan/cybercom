from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel
from products.cycom.inventory.models import Product


class SalesOrder(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Quotation"),
        ("confirmed", "Sales Order"),
        ("delivered", "Delivered"),
        ("invoiced", "Invoiced"),
        ("cancelled", "Cancelled"),
    ]

    # Ported from CyShop. CyShop kept a separate Quotation model that converted
    # into a SalesOrder; Cycom instead models the quotation->order lifecycle on
    # this one record via `status` (draft == Quotation). These fields carry the
    # quotation-specific data CyShop's model had (retail/wholesale pricing tier,
    # quote expiry, printed terms) without forking into a parallel table.
    CUSTOMER_TYPE_CHOICES = [("retail", "Retail"), ("wholesale", "Wholesale")]

    number = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)
    customer_type = models.CharField(
        max_length=20, choices=CUSTOMER_TYPE_CHOICES, default="retail"
    )
    order_date = models.DateField()
    # Quotation expiry — only meaningful while status == "draft".
    valid_until = models.DateField(null=True, blank=True)
    terms = models.TextField(blank=True)
    currency = models.CharField(max_length=10, default="JOD")
    amount_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    salesperson = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    invoice = models.ForeignKey(
        "cycom_ar_ap.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_sales_orders"
        unique_together = [("tenant_id", "number")]
        ordering = ["-order_date", "-created_at"]

    def __str__(self):
        return f"{self.number} — {self.customer_name}"

    def recompute_totals(self, save=True):
        subtotal = sum((l.subtotal for l in self.lines.all()), Decimal("0"))
        tax = sum((l.tax_amount for l in self.lines.all()), Decimal("0"))
        self.amount_subtotal = subtotal.quantize(Decimal("0.01"))
        self.amount_tax = tax.quantize(Decimal("0.01"))
        self.amount_total = (subtotal + tax).quantize(Decimal("0.01"))
        if save:
            self.save(update_fields=["amount_subtotal", "amount_tax", "amount_total", "updated_at"])


class SalesOrderLine(BaseModel):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, blank=True, related_name="sales_order_lines"
    )
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=16)

    class Meta:
        db_table = "cycom_sales_order_lines"
        ordering = ["id"]

    @property
    def subtotal(self) -> Decimal:
        gross = self.quantity * self.unit_price
        net = gross * (Decimal("1") - self.discount_percent / 100)
        return net.quantize(Decimal("0.01"))

    @property
    def tax_amount(self) -> Decimal:
        return (self.subtotal * self.tax_percent / 100).quantize(Decimal("0.01"))
