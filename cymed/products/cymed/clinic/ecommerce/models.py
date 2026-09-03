"""Clinic e-commerce — sell supplements, wellness packages, services online."""
from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel, SoftDeleteMixin


class ClinicProduct(BaseModel, SoftDeleteMixin):
    KIND = [("supplement", "Supplement"), ("skincare", "Skincare"),
            ("wellness", "Wellness package"), ("service", "Service"),
            ("membership", "Membership")]

    tenant_id = models.UUIDField(db_index=True)
    kind = models.CharField(max_length=20, choices=KIND)
    sku = models.CharField(max_length=80, db_index=True)
    name_en = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    description_en = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="SAR")
    stock_qty = models.IntegerField(default=0, help_text="Ignored for services/memberships")
    active = models.BooleanField(default=True, db_index=True)
    image_url = models.URLField(blank=True)

    class Meta:
        db_table = "cymed_clinic_products"
        unique_together = [("tenant_id", "sku")]


class ClinicOrder(BaseModel):
    STATUS = [("cart", "Cart"), ("placed", "Placed"),
              ("paid", "Paid"), ("fulfilling", "Fulfilling"),
              ("shipped", "Shipped"), ("delivered", "Delivered"),
              ("cancelled", "Cancelled"), ("refunded", "Refunded")]

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS, default="cart", db_index=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    vat = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    delivery_address = models.CharField(max_length=400, blank=True)
    bill_id = models.UUIDField(null=True, blank=True)     # links to payments.UnifiedBill
    placed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_clinic_orders"


class ClinicOrderItem(BaseModel):
    order = models.ForeignKey(ClinicOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ClinicProduct, on_delete=models.PROTECT)
    qty = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = "cymed_clinic_order_items"
