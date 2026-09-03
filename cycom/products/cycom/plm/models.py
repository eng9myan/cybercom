from django.db import models

from platform.common.models import BaseModel


class ProductBOM(BaseModel):
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_plm_boms"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product_name} ({self.sku})"


class BomComponent(BaseModel):
    bom = models.ForeignKey(ProductBOM, on_delete=models.CASCADE, related_name="components")
    name = models.CharField(max_length=255)
    qty_needed = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_plm_bom_components"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} x{self.qty_needed}"


class EngineeringChangeOrder(BaseModel):
    STAGE_CHOICES = [
        ("draft", "Draft"),
        ("review", "Under Review"),
        ("approved", "Approved"),
        ("done", "Done"),
    ]

    name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    reason = models.TextField(blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="draft")
    owner = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_plm_ecos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.stage})"
