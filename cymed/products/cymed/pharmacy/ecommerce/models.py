"""CyMed Pharmacy E-commerce & Refill models."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class PharmacyProduct(BaseModel):
    class Kind(models.TextChoices):
        RX = "rx", "Prescription"
        OTC = "otc", "OTC"
        COSMETIC = "cosmetic", "Cosmetic"
        SUPPLEMENT = "supplement", "Supplement"
        DEVICE = "device", "Device"
        BABY = "baby", "Baby"
        OTHER = "other", "Other"

    tenant_id = models.UUIDField(db_index=True)
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.OTC)
    drug_id = models.UUIDField(null=True, blank=True)
    requires_prescription = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="SAR")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))
    stock_qty = models.IntegerField(default=0)
    image_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_pharmacy_ecommerce_pharmacy_product"
        unique_together = [("tenant_id", "sku")]

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"


class RefillRequest(BaseModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        READY_FOR_DELIVERY = "ready_for_delivery", "Ready for Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    original_prescription_id = models.UUIDField(null=True, blank=True)
    drug_id = models.UUIDField(null=True, blank=True)
    drug_name = models.CharField(max_length=255)
    qty = models.IntegerField(default=1)
    delivery_address = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SUBMITTED)
    pharmacist_notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_pharmacy_ecommerce_refill_request"

    def __str__(self) -> str:
        return f"Refill {self.drug_name} ({self.status})"


class Cart(BaseModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CHECKED_OUT = "checked_out", "Checked Out"
        ABANDONED = "abandoned", "Abandoned"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)

    class Meta:
        db_table = "cymed_pharmacy_ecommerce_cart"

    def __str__(self) -> str:
        return f"Cart {self.pk} ({self.status})"


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(PharmacyProduct, on_delete=models.PROTECT, related_name="cart_items")
    qty = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    snapshot_name = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_pharmacy_ecommerce_cart_item"

    def __str__(self) -> str:
        return f"{self.snapshot_name} x{self.qty}"


class PharmacyOrder(BaseModel):
    class Source(models.TextChoices):
        WEB = "web", "Web"
        MOBILE = "mobile", "Mobile"
        PHONE = "phone", "Phone"
        KIOSK = "kiosk", "Kiosk"
        WALKIN = "walkin", "Walk-in"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PLACED = "placed", "Placed"
        PAID = "paid", "Paid"
        DISPENSING = "dispensing", "Dispensing"
        READY = "ready", "Ready"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        RETURNED = "returned", "Returned"
        CANCELLED = "cancelled", "Cancelled"

    class Fulfillment(models.TextChoices):
        PICKUP = "pickup", "Pickup"
        DELIVERY = "delivery", "Delivery"
        MAIL = "mail", "Mail"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    source = models.CharField(max_length=32, choices=Source.choices, default=Source.WEB)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    fulfillment = models.CharField(max_length=32, choices=Fulfillment.choices, default=Fulfillment.PICKUP)
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    vat = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    discount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="SAR")
    payment_ref = models.CharField(max_length=128, blank=True)
    delivery_address = models.JSONField(default=dict, blank=True)
    delivery_slot_start = models.DateTimeField(null=True, blank=True)
    delivery_slot_end = models.DateTimeField(null=True, blank=True)
    delivery_id = models.UUIDField(null=True, blank=True)
    bill_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_ecommerce_pharmacy_order"

    def __str__(self) -> str:
        return f"Order {self.pk} ({self.status})"


class PharmacyOrderItem(BaseModel):
    order = models.ForeignKey(PharmacyOrder, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=255)
    qty = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    is_prescription = models.BooleanField(default=False)
    refill_request_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_ecommerce_pharmacy_order_item"

    def __str__(self) -> str:
        return f"{self.product_name} x{self.qty}"
