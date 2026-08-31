"""
Cycom Catalog — product catalog with categories, units, tax classes,
kit/BOM bundles and size/colour variants.

Ported from CyShop `apps.catalog`. Adapted to Cycom conventions:
- inherits `platform.common.models.BaseModel` (UUIDv4 pk, timestamps,
  required tenant_id) + `SoftDeleteMixin` (is_deleted/soft_delete) via the
  local `CatalogModel` base, instead of CyShop's `BaseEntity`.
- CyShop's per-`Company` foreign key is dropped: Cycom product apps scope by
  `tenant_id` alone (matching `products.cycom.inventory`). Multi-company /
  branch scoping, if needed, is added later at the platform layer.
- `created_by` / `updated_by` / `version` audit columns are dropped to match
  the Cycom base model (audit lives in `platform.audit`).
"""

from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from platform.common.models import BaseModel, SoftDeleteMixin


class CatalogModel(BaseModel, SoftDeleteMixin):
    """Tenant-scoped, soft-deletable base for all catalog entities."""

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class Category(CatalogModel):
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cycom_catalog_categories"
        ordering = ["sort_order", "name"]
        unique_together = [("tenant_id", "slug")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductUnit(CatalogModel):
    """Units of measure: piece, kg, litre, box, etc."""

    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)

    class Meta:
        db_table = "cycom_catalog_units"
        unique_together = [("tenant_id", "abbreviation")]

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class TaxClass(CatalogModel):
    """
    Named tax class (e.g. "Standard", "Exempt", "Reduced").
    `rate` is a configurable decimal (e.g. 0.1600 = 16%).
    A jurisdiction-specific TaxRate table with date ranges will supersede this
    field once wired to `products.cycom.localization`.
    """

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    rate = models.DecimalField(max_digits=5, decimal_places=4, default="0.0000")

    class Meta:
        db_table = "cycom_catalog_tax_classes"
        unique_together = [("tenant_id", "code")]

    def __str__(self):
        return self.name


class Product(CatalogModel):
    PRODUCT_TYPES = [
        ("STORABLE", "Storable Product"),
        ("CONSUMABLE", "Consumable"),
        ("SERVICE", "Service"),
        ("KIT", "Kit / Bundle"),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    unit = models.ForeignKey(
        ProductUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    tax_class = models.ForeignKey(
        TaxClass, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="STORABLE")
    name = models.CharField(max_length=255)
    internal_ref = models.CharField(max_length=100, blank=True)  # internal code / SKU
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    cost_price = models.DecimalField(max_digits=15, decimal_places=4, default="0.0000")
    sell_price = models.DecimalField(max_digits=15, decimal_places=4, default="0.0000")

    # Stock control
    track_stock = models.BooleanField(default=True)
    min_stock_qty = models.DecimalField(max_digits=15, decimal_places=4, default="0.0000")

    # POS visibility
    pos_available = models.BooleanField(default=True)
    pos_category_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cycom_catalog_products"
        ordering = ["name"]
        # internal_ref is blank-able. A plain unique_together would cap a tenant
        # at ONE blank-ref product; a partial constraint enforces uniqueness only
        # when a ref is actually set. (CyShop masked this with its per-Company FK,
        # which we dropped.)
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "internal_ref"],
                condition=~Q(internal_ref=""),
                name="uniq_catalog_product_ref_per_tenant",
            )
        ]

    def __str__(self):
        return self.name


class KitComponent(CatalogModel):
    """
    One raw-material line in a KIT product's bill of materials.
    Selling `quantity` units of `product` (a KIT) consumes
    `quantity_per_unit * quantity` units of `component_product`.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bom_components")
    component_product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="used_in_kits"
    )
    quantity_per_unit = models.DecimalField(max_digits=15, decimal_places=4, default="1.0000")

    class Meta:
        db_table = "cycom_catalog_kit_components"
        ordering = ["component_product__name"]
        unique_together = [("product", "component_product")]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.product_id == self.component_product_id:
            raise ValidationError("A product cannot be a component of itself.")
        if self.quantity_per_unit <= 0:
            raise ValidationError({"quantity_per_unit": "Quantity per unit must be positive."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} needs {self.quantity_per_unit} x {self.component_product.name}"


class ProductVariant(CatalogModel):
    """Optional size/colour/SKU variants of a base Product."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    cost_price = models.DecimalField(max_digits=15, decimal_places=4, default="0.0000")
    sell_price = models.DecimalField(max_digits=15, decimal_places=4, default="0.0000")
    attributes = models.JSONField(default=dict)  # {"color": "red", "size": "L"}

    class Meta:
        db_table = "cycom_catalog_variants"
        ordering = ["name"]

    def __str__(self):
        return f"{self.product.name} – {self.name}"
