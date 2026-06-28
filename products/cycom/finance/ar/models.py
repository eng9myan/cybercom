from django.db import models
from platform.common.models import BaseModel


class Customer(BaseModel):
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    customer_code = models.CharField(max_length=50)
    tax_id = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payment_terms_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_finance_ar_customers"

    def __str__(self):
        return f"{self.customer_code} - {self.name}"


class Invoice(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("partial", "Partial"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    currency = models.CharField(max_length=3, default="SAR")

    class Meta:
        db_table = "cycom_finance_ar_invoices"

    def __str__(self):
        return f"{self.invoice_number} - {self.customer}"


class InvoiceLine(BaseModel):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="lines"
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_finance_ar_invoice_lines"

    def __str__(self):
        return f"Line {self.id} - {self.description[:50]}"


class Payment(BaseModel):
    METHOD_CHOICES = [
        ("cash", "Cash"),
        ("bank", "Bank Transfer"),
        ("card", "Card"),
        ("insurance", "Insurance"),
        ("wallet", "Wallet"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="payments"
    )
    invoice = models.ForeignKey(
        Invoice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_finance_ar_payments"

    def __str__(self):
        return f"Payment {self.id} - {self.customer} ({self.amount})"


class ARAgingBucket(BaseModel):
    BUCKET_CHOICES = [
        ("current", "Current"),
        ("1-30", "1-30 Days"),
        ("31-60", "31-60 Days"),
        ("61-90", "61-90 Days"),
        ("90+", "90+ Days"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="aging_buckets"
    )
    bucket_label = models.CharField(max_length=10, choices=BUCKET_CHOICES)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_finance_ar_aging_buckets"

    def __str__(self):
        return f"{self.customer} - {self.bucket_label}: {self.amount}"
