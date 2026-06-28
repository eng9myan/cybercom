from django.db import models
from platform.common.models import BaseModel


class Warehouse(BaseModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_inventory_warehouses"

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockItem(BaseModel):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_items",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    unit = models.CharField(max_length=20, default="pcs")
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_inventory_stock_items"

    def __str__(self):
        return f"{self.sku} - {self.name}"


class StockMovement(BaseModel):
    MOVEMENT_TYPE_CHOICES = [
        ("receipt", "Receipt (In)"),
        ("issue", "Issue (Out)"),
        ("transfer", "Transfer"),
        ("adjustment", "Adjustment"),
    ]

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name="movements",
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    reference_id = models.UUIDField(null=True, blank=True)  # Can refer to PO line, Invoice line, etc.
    movement_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_inventory_stock_movements"

    def save(self, *args, **kwargs):
        # Update stock item balance upon movement
        is_new = self._state.adding
        if is_new:
            # Adjust item quantity
            if self.movement_type in ("receipt", "adjustment"):
                self.stock_item.quantity += self.quantity
            elif self.movement_type == "issue":
                self.stock_item.quantity -= self.quantity
            self.stock_item.save(update_fields=["quantity"])
        super().save(*args, **kwargs)
