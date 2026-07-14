from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from apps.tenants.models import BaseEntity, Company, Branch
from apps.catalog.models import Product, ProductVariant


class PosSession(BaseEntity):
    STATUS = [('OPEN', 'Open'), ('CLOSED', 'Closed')]

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='pos_sessions')
    branch = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name='pos_sessions', null=True, blank=True
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pos_sessions'
    )
    name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default='OPEN')
    opening_float = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    closing_float = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    opening_at = models.DateTimeField(auto_now_add=True)
    closing_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-opening_at']

    def save(self, *args, **kwargs):
        if not self.name:
            count = PosSession.objects.filter(
                tenant_id=self.tenant_id, company=self.company
            ).count()
            self.name = f"Session #{count + 1:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PosOrder(BaseEntity):
    STATUS = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    SOURCE = [
        ('POS', 'POS Terminal'),
        ('KIOSK', 'Self-Service Kiosk'),
        ('ONLINE', 'Online Order'),
    ]

    session = models.ForeignKey(
        PosSession, on_delete=models.PROTECT, related_name='orders', null=True, blank=True
    )
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='pos_orders')
    branch = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name='pos_orders', null=True, blank=True
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='pos_orders', null=True, blank=True
    )
    order_number = models.CharField(max_length=50, blank=True, db_index=True)
    source = models.CharField(max_length=20, choices=SOURCE, default='POS')
    status = models.CharField(max_length=20, choices=STATUS, default='DRAFT')
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=50, blank=True)
    table_ref = models.CharField(max_length=50, blank=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    discount_amount = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    total = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    KITCHEN_STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('READY', 'Ready'),
        ('SERVED', 'Served'),
    ]
    kitchen_status = models.CharField(max_length=20, choices=KITCHEN_STATUS, default='PENDING')

    class Meta:
        ordering = ['-created_at']
        unique_together = [('tenant_id', 'order_number')]

    def save(self, *args, **kwargs):
        if not self.order_number:
            prefix = timezone.now().strftime('%Y%m%d')
            self.order_number = f"ORD-{prefix}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)

    def recalculate(self):
        lines = self.lines.filter(is_deleted=False)
        subtotal = sum((l.line_subtotal for l in lines), Decimal('0'))
        tax = sum((l.line_tax for l in lines), Decimal('0'))
        discount = Decimal(str(self.discount_amount or 0))
        self.subtotal = subtotal
        self.tax_amount = tax
        self.total = subtotal + tax - discount
        self.save()

    def __str__(self):
        return self.order_number or str(self.id)


class PosOrderLine(BaseEntity):
    order = models.ForeignKey(PosOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='pos_order_lines')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, null=True, blank=True,
        related_name='pos_order_lines'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default='0.00')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default='0.0000')
    notes = models.TextField(blank=True)

    @property
    def line_subtotal(self):
        discounted = self.unit_price * (1 - self.discount_percent / Decimal('100'))
        return (self.quantity * discounted).quantize(Decimal('0.0001'))

    @property
    def line_tax(self):
        return (self.line_subtotal * self.tax_rate).quantize(Decimal('0.0001'))

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class PosPayment(BaseEntity):
    METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('MOBILE', 'Mobile Payment'),
        ('LOYALTY', 'Loyalty Points'),
        ('CREDIT', 'Store Credit'),
    ]

    order = models.ForeignKey(PosOrder, on_delete=models.PROTECT, related_name='payments')
    method = models.CharField(max_length=20, choices=METHODS)
    amount = models.DecimalField(max_digits=15, decimal_places=4)
    reference = models.CharField(max_length=255, blank=True)
    change_given = models.DecimalField(max_digits=15, decimal_places=4, default='0.0000')

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({'amount': 'Payment amount must be positive.'})

    def __str__(self):
        return f"{self.method} {self.amount}"


class PosReceipt(BaseEntity):
    order = models.OneToOneField(PosOrder, on_delete=models.PROTECT, related_name='receipt')
    receipt_number = models.CharField(max_length=50, db_index=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    emailed_at = models.DateTimeField(null=True, blank=True)
    qr_data = models.TextField(blank=True)

    class Meta:
        unique_together = [('tenant_id', 'receipt_number')]

    def __str__(self):
        return self.receipt_number


class Device(BaseEntity):
    """
    A registered fullscreen terminal/screen at a branch (POS terminal, kitchen display,
    waiter handheld, customer-facing display, warehouse scanner, self-order kiosk).
    Each device_type maps to a standalone Next.js route outside the manager shell.
    """

    DEVICE_TYPES = [
        ('POS', 'POS Terminal'),
        ('KDS', 'Kitchen Display'),
        ('WAITER', 'Waiter Handheld'),
        ('CUSTOMER_DISPLAY', 'Customer-Facing Display'),
        ('WAREHOUSE_SCANNER', 'Warehouse Scanner'),
        ('SELF_ORDER', 'Self-Order Kiosk'),
    ]
    ROUTE_BY_TYPE = {
        'POS': '/pos-terminal',
        'KDS': '/kds',
        'WAITER': '/waiter',
        'CUSTOMER_DISPLAY': '/customer-display',
        'WAREHOUSE_SCANNER': '/warehouse-scanner',
        'SELF_ORDER': '/self-order',
    }

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='devices')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['branch', 'device_type', 'name']
        unique_together = [('tenant_id', 'company', 'code')]

    @property
    def route(self):
        return self.ROUTE_BY_TYPE.get(self.device_type, '/')

    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()} @ {self.branch})"
