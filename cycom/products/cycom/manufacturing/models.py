from django.db import models

from platform.common.models import BaseModel
from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, Warehouse


class BillOfMaterial(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="boms")
    name = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=14, decimal_places=4, default=1,
        help_text="How many units of `product` this BoM produces per run.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_manufacturing_boms"
        ordering = ["product__sku", "name"]

    def __str__(self):
        return f"{self.name} ({self.product.sku})"


class BOMComponent(BaseModel):
    bom = models.ForeignKey(BillOfMaterial, on_delete=models.CASCADE, related_name="components")
    component = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="used_in_boms")
    quantity = models.DecimalField(
        max_digits=14, decimal_places=4,
        help_text="Quantity of `component` needed per one BoM run (see BillOfMaterial.quantity).",
    )

    class Meta:
        db_table = "cycom_manufacturing_bom_components"

    def __str__(self):
        return f"{self.component.sku} x{self.quantity}"


class ManufacturingOrder(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    bom = models.ForeignKey(BillOfMaterial, on_delete=models.PROTECT, related_name="orders")
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="manufacturing_orders")
    wip_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="+",
        help_text="Work-in-progress clearing account — debited on component consumption, credited on finished-goods receipt.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    scheduled_date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cycom_manufacturing_orders"
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"MO {self.id} — {self.bom.product.sku} x{self.quantity} ({self.status})"
