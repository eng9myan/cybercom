import uuid

from django.db import models


class CartStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CHECKED_OUT = "checked_out", "Checked Out"
    ABANDONED = "abandoned", "Abandoned"


class Cart(models.Model):
    """
    Master spec section 15: "Initial implementation may restrict each cart
    to one merchant unless a multi-merchant settlement and delivery model
    is fully implemented." That model doesn't exist yet (split
    authorization/capture/refunds, multiple delivery jobs, combined
    tracking — all Phase 6/7), so this cart is single-store by
    construction: store_id is set from the first item added and every
    subsequent add is rejected if it doesn't match.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(db_index=True)
    store_id = models.UUIDField(null=True, blank=True)
    tenant_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=CartStatus.choices, default=CartStatus.ACTIVE)
    order_id = models.UUIDField(null=True, blank=True, help_text="Set once checked out.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_cart"
        indexes = [models.Index(fields=["customer_id", "status"])]

    def __str__(self):
        return f"Cart({self.id}, {self.status})"

    @property
    def is_empty(self) -> bool:
        return not self.items.exists()


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    product_name_snapshot = models.CharField(max_length=300, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    item_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = "cymart_cart_item"
        constraints = [
            models.UniqueConstraint(fields=["cart", "product_id"], name="unique_product_per_cart")
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product_name_snapshot or self.product_id}"
