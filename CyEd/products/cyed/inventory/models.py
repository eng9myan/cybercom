from django.db import models

from platform.common.models import BaseModel


class InventoryItem(BaseModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=30, default="each")
    on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    location = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cyed_inventory_items"
        ordering = ["name"]

    @property
    def needs_reorder(self) -> bool:
        return self.on_hand <= self.reorder_level

    def __str__(self):
        return f"{self.name} ({self.on_hand} {self.unit})"


class StockMove(BaseModel):
    MOVE_TYPES = [("in", "Stock In"), ("out", "Stock Out"), ("adjust", "Adjustment")]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="moves")
    move_type = models.CharField(max_length=10, choices=MOVE_TYPES, default="in")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # signed change
    reason = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cyed_stock_moves"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.item_id} {self.move_type} {self.quantity}"
