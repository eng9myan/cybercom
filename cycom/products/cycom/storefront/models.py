import secrets

from django.db import models

from platform.common.models import BaseModel
from products.cycom.catalog.models import Product
from products.cycom.sales.models import SalesOrder


def _generate_token() -> str:
    return secrets.token_urlsafe(24)


class Cart(BaseModel):
    """An anonymous shopper's cart, reachable only by its unguessable
    token — same public-link pattern as esign.SignRequest. No login
    required to browse or check out."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("checked_out", "Checked Out"),
    ]

    token = models.CharField(max_length=64, unique=True, default=_generate_token, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    order = models.ForeignKey(
        SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_storefront_carts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cart {self.token[:8]}… ({self.status})"


class CartLine(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cycom_storefront_cart_lines"
        unique_together = [("cart", "product")]
        ordering = ["id"]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
