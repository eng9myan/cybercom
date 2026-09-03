"""Domain models for the CyMed DTC (direct-to-consumer) test catalog."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class DtcCategory(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    name_ar = models.CharField(max_length=128, blank=True)
    icon_url = models.URLField(blank=True)
    display_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_lab_dtc_catalog_dtc_category"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class DtcProduct(BaseModel):
    class Kind(models.TextChoices):
        WELLNESS_PANEL = "wellness_panel", "Wellness Panel"
        VITAMIN_PANEL = "vitamin_panel", "Vitamin Panel"
        HORMONAL_PANEL = "hormonal_panel", "Hormonal Panel"
        GENETIC = "genetic", "Genetic"
        NUTRIGENOMIC = "nutrigenomic", "Nutrigenomic"
        MICROBIOME = "microbiome", "Microbiome"
        ALLERGY = "allergy", "Allergy"
        FERTILITY = "fertility", "Fertility"
        STRESS = "stress", "Stress"
        LONGEVITY = "longevity", "Longevity"

    class SpecimenType(models.TextChoices):
        BLOOD = "blood", "Blood"
        SALIVA = "saliva", "Saliva"
        STOOL = "stool", "Stool"
        SWAB = "swab", "Swab"
        URINE = "urine", "Urine"
        OTHER = "other", "Other"

    class CollectionMode(models.TextChoices):
        HOME_KIT = "home_kit", "Home Kit"
        IN_LAB = "in_lab", "In Lab"
        HOME_VISIT = "home_visit", "Home Visit"

    tenant_id = models.UUIDField(db_index=True)
    category = models.ForeignKey(
        DtcCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    tests_included = models.JSONField(default=list, blank=True)
    specimen_type = models.CharField(max_length=32, choices=SpecimenType.choices)
    collection_mode = models.CharField(max_length=32, choices=CollectionMode.choices)
    turnaround_days = models.IntegerField(default=5)
    includes_consultation = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=3, default="SAR")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))
    stock_qty = models.IntegerField(default=-1)
    active = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)

    class Meta:
        db_table = "cymed_lab_dtc_catalog_dtc_product"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class DtcKit(BaseModel):
    class Status(models.TextChoices):
        IN_STOCK = "in_stock", "In Stock"
        DISPATCHED = "dispatched", "Dispatched"
        ACTIVATED = "activated", "Activated"
        RETURNED_FULL = "returned_full", "Returned Full"
        RETURNED_EMPTY = "returned_empty", "Returned Empty"
        EXPIRED = "expired", "Expired"
        LOST = "lost", "Lost"

    tenant_id = models.UUIDField(db_index=True)
    product = models.ForeignKey(
        DtcProduct,
        on_delete=models.CASCADE,
        related_name="kits",
    )
    kit_barcode = models.CharField(max_length=64, unique=True)
    lot_number = models.CharField(max_length=64, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.IN_STOCK,
    )

    class Meta:
        db_table = "cymed_lab_dtc_catalog_dtc_kit"

    def __str__(self) -> str:
        return f"Kit {self.kit_barcode} ({self.status})"


class DtcOrder(BaseModel):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        PAID = "paid", "Paid"
        KIT_DISPATCHED = "kit_dispatched", "Kit Dispatched"
        KIT_DELIVERED = "kit_delivered", "Kit Delivered"
        KIT_ACTIVATED = "kit_activated", "Kit Activated"
        SAMPLE_RECEIVED = "sample_received", "Sample Received"
        ANALYSING = "analysing", "Analysing"
        RESULTS_READY = "results_ready", "Results Ready"
        DELIVERED_TO_PATIENT = "delivered_to_patient", "Delivered To Patient"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    product = models.ForeignKey(
        DtcProduct,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    kit = models.ForeignKey(
        DtcKit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    shipping_address = models.JSONField(default=dict, blank=True)
    return_pickup_scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PLACED,
    )
    payment_ref = models.CharField(max_length=128, blank=True)
    bill_id = models.UUIDField(null=True, blank=True)
    consultation_scheduled_at = models.DateTimeField(null=True, blank=True)
    consultation_notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_dtc_catalog_dtc_order"

    def __str__(self) -> str:
        return f"DTC Order {self.id} ({self.status})"
