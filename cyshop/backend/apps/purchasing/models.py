from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.tenants.models import BaseEntity, Company, Branch
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import Warehouse, StockLocation, StockMovement


class Vendor(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vendors')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    payment_terms_days = models.PositiveIntegerField(default=30)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [('tenant_id', 'company', 'code')]

    def __str__(self):
        return self.name


class PurchaseOrder(BaseEntity):
    STATUS = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('PARTIAL', 'Partially Received'),
        ('RECEIVED', 'Fully Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='purchase_orders')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='purchase_orders', null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='purchase_orders', null=True, blank=True)

    po_number = models.CharField(max_length=50, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS, default='DRAFT')
    currency = models.CharField(max_length=10, default='USD')
    order_date = models.DateField(default=timezone.localdate)
    expected_date = models.DateField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    total = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('tenant_id', 'po_number')]

    def save(self, *args, **kwargs):
        if not self.po_number:
            prefix = timezone.now().strftime('%Y%m%d')
            self.po_number = f"PO-{prefix}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)

    def recalculate(self):
        lines = self.lines.filter(is_deleted=False)
        subtotal = sum((ln.line_subtotal for ln in lines), Decimal('0'))
        tax = sum((ln.line_tax for ln in lines), Decimal('0'))
        self.subtotal = subtotal
        self.tax_amount = tax
        self.total = subtotal + tax
        self.save()

    def update_receipt_status(self):
        lines = self.lines.filter(is_deleted=False)
        if not lines.exists():
            return
        all_received = all(ln.received_qty >= ln.quantity for ln in lines)
        any_received = any(ln.received_qty > Decimal('0') for ln in lines)
        if all_received:
            self.status = 'RECEIVED'
        elif any_received:
            self.status = 'PARTIAL'
        self.save(update_fields=['status', 'updated_at', 'version'])

    def __str__(self):
        return self.po_number or str(self.id)


class PurchaseOrderLine(BaseEntity):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchase_order_lines')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, null=True, blank=True,
        related_name='purchase_order_lines'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default='0.0000')
    received_qty = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    notes = models.TextField(blank=True)

    @property
    def line_subtotal(self):
        return (self.quantity * self.unit_cost).quantize(Decimal('0.0001'))

    @property
    def line_tax(self):
        return (self.line_subtotal * self.tax_rate).quantize(Decimal('0.0001'))

    @property
    def outstanding_qty(self):
        return max(Decimal('0'), self.quantity - self.received_qty)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class GoodsReceipt(BaseEntity):
    STATUS = [('DRAFT', 'Draft'), ('POSTED', 'Posted')]

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='receipts')
    grn_number = models.CharField(max_length=50, blank=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS, default='DRAFT')
    received_at = models.DateTimeField(default=timezone.now)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='goods_receipts')
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='goods_receipts')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-received_at']
        unique_together = [('tenant_id', 'grn_number')]

    def save(self, *args, **kwargs):
        if not self.grn_number:
            prefix = timezone.now().strftime('%Y%m%d')
            self.grn_number = f"GRN-{prefix}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)

    def post(self):
        if self.status == 'POSTED':
            raise ValidationError('GRN already posted.')
        with transaction.atomic():
            for line in self.grn_lines.filter(is_deleted=False):
                StockMovement.objects.create(
                    tenant_id=self.tenant_id,
                    product=line.product,
                    variant=line.variant,
                    to_location=self.location,
                    warehouse=self.warehouse,
                    quantity=line.received_qty,
                    unit_cost=line.unit_cost,
                    movement_type='RECEIPT',
                    reference=self.grn_number,
                    notes=f"GRN {self.grn_number} / PO {self.purchase_order.po_number}",
                )
                po_line = line.po_line
                po_line.received_qty = Decimal(str(po_line.received_qty or 0)) + line.received_qty
                po_line.save(update_fields=['received_qty', 'updated_at', 'version'])

            self.status = 'POSTED'
            self.save(update_fields=['status', 'updated_at', 'version'])
            self.purchase_order.update_receipt_status()

    def __str__(self):
        return self.grn_number or str(self.id)


class GoodsReceiptLine(BaseEntity):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='grn_lines')
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT, related_name='grn_lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='grn_lines')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, null=True, blank=True,
        related_name='grn_lines'
    )
    received_qty = models.DecimalField(max_digits=15, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4)

    def clean(self):
        if self.received_qty <= 0:
            raise ValidationError({'received_qty': 'Received quantity must be positive.'})
        outstanding = self.po_line.outstanding_qty
        if self.received_qty > outstanding and outstanding > 0:
            raise ValidationError({
                'received_qty': f'Cannot receive {self.received_qty}; outstanding is {outstanding}.'
            })

    def __str__(self):
        return f"{self.product.name} x{self.received_qty}"
