import uuid
from django.db import models
from platform.common.models import BaseModel


class PatientInvoice(BaseModel):
    INVOICE_TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('procedure', 'Procedure'),
        ('lab', 'Lab'),
        ('imaging', 'Imaging'),
        ('pharmacy', 'Pharmacy'),
        ('admission', 'Admission'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    cycom_invoice_id = models.CharField(max_length=255, db_index=True)
    invoice_number = models.CharField(max_length=100, unique=True, db_index=True)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, default='consultation')
    provider_name = models.CharField(max_length=255)
    service_date = models.DateField(null=True, blank=True)
    amount_total = models.DecimalField(max_digits=12, decimal_places=2)
    amount_covered_insurance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_patient_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField(null=True, blank=True)
    pdf_url = models.URLField(max_length=2000, blank=True)
    insurance_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'cymed_portal_invoices'
        indexes = [
            models.Index(fields=['account_id', 'status', 'due_date']),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.status}"


class PaymentTransaction(BaseModel):
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('digital_wallet', 'Digital Wallet'),
        ('cash', 'Cash'),
        ('insurance', 'Insurance'),
        ('installment', 'Installment'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    invoice = models.ForeignKey(
        PatientInvoice,
        related_name='transactions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    transaction_reference = models.CharField(max_length=255, unique=True, db_index=True)
    cycom_transaction_id = models.CharField(max_length=255, blank=True)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='credit_card')
    payment_gateway = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    gateway_response = models.JSONField(default=dict)
    receipt_url = models.URLField(max_length=2000, blank=True)

    class Meta:
        db_table = 'cymed_portal_payment_transactions'
        indexes = [
            models.Index(fields=['account_id', 'status', 'paid_at']),
        ]

    def __str__(self):
        return f"Transaction {self.transaction_reference} - {self.status}"


class PaymentMethod(BaseModel):
    METHOD_TYPE_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_account', 'Bank Account'),
        ('digital_wallet', 'Digital Wallet'),
    ]

    account_id = models.UUIDField(db_index=True)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPE_CHOICES)
    display_name = models.CharField(max_length=100)
    last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=30, blank=True)
    expiry_month = models.PositiveSmallIntegerField(null=True, blank=True)
    expiry_year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    gateway_token = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'cymed_portal_payment_methods'
        indexes = [
            models.Index(fields=['account_id', 'is_active']),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.method_type})"


class InstallmentPlan(BaseModel):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
        ('cancelled', 'Cancelled'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    invoice = models.ForeignKey(
        PatientInvoice,
        related_name='installment_plans',
        on_delete=models.CASCADE,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    installment_count = models.PositiveSmallIntegerField()
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    first_payment_date = models.DateField()
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    installments_paid = models.PositiveSmallIntegerField(default=0)
    next_payment_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_installment_plans'
        indexes = [
            models.Index(fields=['account_id', 'status']),
        ]

    def __str__(self):
        return f"Installment Plan - Invoice {self.invoice_id} ({self.status})"
