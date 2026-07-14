from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.tenants.models import BaseEntity, Company, Branch
from apps.catalog.models import Product, ProductVariant


class Warehouse(BaseEntity):
    """
    Full warehouse entity. Replaces the WarehousePlaceholder in apps.tenants.
    Existing placeholder records are migrated separately; this model takes over.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='real_warehouses')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='inv_warehouses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [('tenant_id', 'company', 'code')]

    def __str__(self):
        return f"{self.code} – {self.name}"


class StockLocation(BaseEntity):
    """A zone or shelf inside a warehouse (e.g. SHELF-A1, RECEIVING, PRODUCTION)."""

    LOCATION_TYPES = [
        ('INTERNAL', 'Internal'),
        ('RECEIVING', 'Receiving / Input'),
        ('OUTPUT', 'Output / Dispatch'),
        ('VIRTUAL', 'Virtual / Loss'),
    ]

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default='INTERNAL')

    class Meta:
        ordering = ['code']
        unique_together = [('warehouse', 'code')]

    def __str__(self):
        return f"{self.warehouse.code}/{self.code}"


class StockLevel(BaseEntity):
    """
    Current quantity of a product (or variant) at a specific location.
    Updated atomically every time a StockMovement is posted.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_levels')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_levels'
    )
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE, related_name='stock_levels')
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    reserved_quantity = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')

    class Meta:
        unique_together = [('product', 'variant', 'location')]

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def __str__(self):
        label = self.variant.name if self.variant else self.product.name
        return f"{label} @ {self.location} = {self.quantity}"


class StockMovement(BaseEntity):
    """
    Double-entry style stock journal. Every quantity change produces one movement record.
    Positive quantity always means goods moving INTO to_location;
    from_location being null means a receipt from vendor / production.
    to_location being null means a consumption / loss (out of system).
    """

    MOVEMENT_TYPES = [
        ('RECEIPT', 'Vendor Receipt'),
        ('ISSUE', 'Issue / Sale Consumption'),
        ('TRANSFER', 'Internal Transfer'),
        ('ADJUSTMENT', 'Manual Adjustment'),
        ('PRODUCTION_IN', 'Production Output'),
        ('PRODUCTION_OUT', 'Production Consumption'),
        ('RETURN_IN', 'Customer Return In'),
        ('RETURN_OUT', 'Return to Vendor'),
        ('OPENING', 'Opening Balance'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_movements'
    )
    from_location = models.ForeignKey(
        StockLocation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='movements_out'
    )
    to_location = models.ForeignKey(
        StockLocation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='movements_in'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # Denormalized for reporting without joins
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements'
    )

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be positive.'})
        if self.from_location is None and self.to_location is None:
            raise ValidationError('At least one of from_location or to_location must be set.')

    def save(self, *args, **kwargs):
        self.full_clean()
        from django.db import transaction
        with transaction.atomic():
            super().save(*args, **kwargs)
            self._apply_stock_levels()

    def _apply_stock_levels(self):
        """Update StockLevel rows to reflect this movement."""
        if self.from_location:
            level, _ = StockLevel.objects.select_for_update().get_or_create(
                product=self.product,
                variant=self.variant,
                location=self.from_location,
                defaults={'tenant_id': self.tenant_id, 'quantity': 0},
            )
            level.quantity -= self.quantity
            level.save(update_fields=['quantity', 'updated_at', 'version'])

        if self.to_location:
            level, _ = StockLevel.objects.select_for_update().get_or_create(
                product=self.product,
                variant=self.variant,
                location=self.to_location,
                defaults={'tenant_id': self.tenant_id, 'quantity': 0},
            )
            level.quantity += self.quantity
            level.save(update_fields=['quantity', 'updated_at', 'version'])

    def __str__(self):
        return f"{self.movement_type} {self.quantity} x {self.product.name} ({self.reference or self.id})"


class StockTransfer(BaseEntity):
    """
    Two-phase inter-branch transfer: dispatch debits the source location immediately
    (goods leave the source's stock), receive credits the destination once confirmed.
    While IN_TRANSIT, the quantity exists in neither location's StockLevel — matching
    the real-world state of goods on a truck between branches.
    """

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_TRANSIT', 'In Transit'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    transfer_number = models.CharField(max_length=50, blank=True, db_index=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_transfers')
    from_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_out')
    to_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_in')
    from_location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='transfers_out')
    to_location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='transfers_in')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_transfers')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_transfers'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True)

    dispatch_movement = models.OneToOneField(
        StockMovement, on_delete=models.PROTECT, null=True, blank=True, related_name='transfer_dispatch'
    )
    receive_movement = models.OneToOneField(
        StockMovement, on_delete=models.PROTECT, null=True, blank=True, related_name='transfer_receipt'
    )
    dispatched_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('tenant_id', 'transfer_number')]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be positive.'})
        if self.from_location_id == self.to_location_id:
            raise ValidationError('Source and destination locations must differ.')

    def dispatch(self, user=None):
        """Debit the source location and mark the transfer in transit."""
        if self.status != 'DRAFT' or self.dispatch_movement_id:
            raise ValidationError('Transfer already dispatched.')
        movement = StockMovement.objects.create(
            product=self.product, variant=self.variant,
            from_location=self.from_location, to_location=None,
            quantity=self.quantity, movement_type='ISSUE',
            reference=self.transfer_number,
            notes=f'Dispatch for transfer {self.transfer_number} to {self.to_branch}',
            warehouse=self.from_location.warehouse,
            tenant_id=self.tenant_id, created_by=user,
        )
        from django.utils import timezone
        self.dispatch_movement = movement
        self.dispatched_at = timezone.now()
        self.status = 'IN_TRANSIT'
        self.save(update_fields=['dispatch_movement', 'dispatched_at', 'status', 'updated_at', 'version'])

    def receive(self, user=None):
        """Credit the destination location and mark the transfer complete."""
        if self.status != 'IN_TRANSIT' or self.receive_movement_id:
            raise ValidationError('Transfer is not in transit.')
        movement = StockMovement.objects.create(
            product=self.product, variant=self.variant,
            from_location=None, to_location=self.to_location,
            quantity=self.quantity, movement_type='RECEIPT',
            reference=self.transfer_number,
            notes=f'Receipt for transfer {self.transfer_number} from {self.from_branch}',
            warehouse=self.to_location.warehouse,
            tenant_id=self.tenant_id, created_by=user,
        )
        from django.utils import timezone
        self.receive_movement = movement
        self.received_at = timezone.now()
        self.status = 'COMPLETED'
        self.save(update_fields=['receive_movement', 'received_at', 'status', 'updated_at', 'version'])

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            from django.utils import timezone as tz
            prefix = tz.now().strftime('%Y%m%d')
            self.transfer_number = f"TRF-{prefix}-{str(self.id)[:8].upper()}"
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transfer_number} ({self.status}) {self.quantity} x {self.product.name}"
