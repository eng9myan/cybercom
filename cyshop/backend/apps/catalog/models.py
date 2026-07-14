from django.db import models
from django.utils.text import slugify
from apps.tenants.models import BaseEntity, Company


class Category(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='categories')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        unique_together = [('tenant_id', 'company', 'slug')]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductUnit(BaseEntity):
    """Units of measure: piece, kg, litre, box, etc."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_units')
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)

    class Meta:
        unique_together = [('tenant_id', 'company', 'abbreviation')]

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class TaxClass(BaseEntity):
    """
    Named tax class (e.g. "Standard", "Exempt", "Reduced").
    `rate` is a configurable decimal (e.g. 0.1600 = 16%).
    A jurisdiction-specific TaxRate table with date ranges will
    supersede this field in the Accounting phase.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_classes')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    rate = models.DecimalField(max_digits=5, decimal_places=4, default='0.0000')

    class Meta:
        unique_together = [('tenant_id', 'company', 'code')]

    def __str__(self):
        return self.name


class Product(BaseEntity):
    PRODUCT_TYPES = [
        ('STORABLE', 'Storable Product'),
        ('CONSUMABLE', 'Consumable'),
        ('SERVICE', 'Service'),
        ('KIT', 'Kit / Bundle'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    unit = models.ForeignKey(
        ProductUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    tax_class = models.ForeignKey(
        TaxClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='STORABLE')
    name = models.CharField(max_length=255)
    internal_ref = models.CharField(max_length=100, blank=True)  # internal code / SKU
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    cost_price = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    sell_price = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')

    # Stock control
    track_stock = models.BooleanField(default=True)
    min_stock_qty = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')

    # POS visibility
    pos_available = models.BooleanField(default=True)
    pos_category_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['name']
        unique_together = [('tenant_id', 'company', 'internal_ref')]

    def __str__(self):
        return self.name


class KitComponent(BaseEntity):
    """
    One raw-material line in a KIT product's bill of materials.
    Selling `quantity` units of `product` (a KIT) consumes
    `quantity_per_unit * quantity` units of `component_product`.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_components')
    component_product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='used_in_kits')
    quantity_per_unit = models.DecimalField(max_digits=15, decimal_places=4, default='1.0000')

    class Meta:
        ordering = ['component_product__name']
        unique_together = [('product', 'component_product')]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.product_id == self.component_product_id:
            raise ValidationError('A product cannot be a component of itself.')
        if self.quantity_per_unit <= 0:
            raise ValidationError({'quantity_per_unit': 'Quantity per unit must be positive.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} needs {self.quantity_per_unit} x {self.component_product.name}"


class ProductVariant(BaseEntity):
    """Optional size/colour/SKU variants of a base Product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    cost_price = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    sell_price = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    attributes = models.JSONField(default=dict)  # {"color": "red", "size": "L"}

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} – {self.name}"
