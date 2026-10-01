"""A minimal local merchant catalog for full-stack testing.

Master spec section 15 assumes products/stores live in an external
CyShop/CyCom catalog service, referenced by cart/orders only as bare
UUIDs (store_id, tenant_id, product_id) — no such service exists in
this sandbox. This app fills that gap with a real, seeded catalog (25
Jordan restaurants + 3 hypermarkets, scraped/grounded from real
merchant sites) so the whole order flow — search, cart, diet shield,
checkout, dispatch, tracking — can be exercised end to end locally.

Product.id is deliberately the same value cart/orders/dietshield.
NutritionFact already treat as an opaque product_id — this app is the
thing that UUID actually resolves to.
"""

import uuid

from django.db import models


class MerchantKind(models.TextChoices):
    RESTAURANT = "restaurant", "Restaurant"
    HYPERMARKET = "hypermarket", "Hypermarket"


class Merchant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # One tenant per merchant in this test catalog — kept as a distinct
    # field (not reused from id) because cart/orders treat store_id and
    # tenant_id as independently meaningful, even when they coincide here.
    tenant_id = models.UUIDField(default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=12, choices=MerchantKind.choices)
    cuisine = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, default="Amman")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    # Where a seeded item's real name/price/category came from, for
    # provenance — blank for hand-curated (e.g. restaurant menus).
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_merchant"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="products")

    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=40, blank=True)
    category = models.CharField(max_length=80, blank=True)
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_merchant_product"
        indexes = [models.Index(fields=["merchant", "is_active"])]
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.merchant.name})"
