from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel
from products.cycom.inventory.models import Product, Warehouse


class RentalOrder(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("picked_up", "Picked Up"),
        ("returned", "Returned"),
        ("cancelled", "Cancelled"),
    ]

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_rental_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rental for {self.customer_name} ({self.status})"


class RentalOrderLine(BaseModel):
    order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="rental_lines")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="rental_lines")
    quantity = models.PositiveIntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    late_fee_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    returned_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cycom_rental_order_lines"
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.product.sku} x{self.quantity} ({self.start_date} to {self.end_date})"

    @property
    def rental_days(self):
        return max((self.end_date - self.start_date).days, 1)

    @property
    def subtotal(self):
        return (self.daily_rate * self.quantity * self.rental_days).quantize(Decimal("0.01"))

    @property
    def late_days(self):
        if self.returned_date and self.returned_date > self.end_date:
            return (self.returned_date - self.end_date).days
        return 0

    @property
    def late_fee(self):
        return (self.late_fee_per_day * self.quantity * self.late_days).quantize(Decimal("0.01"))

    @property
    def total(self):
        return self.subtotal + self.late_fee
