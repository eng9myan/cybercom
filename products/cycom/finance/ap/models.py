from django.db import models
from platform.common.models import BaseModel


class Vendor(BaseModel):
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    vendor_code = models.CharField(max_length=50)
    tax_id = models.CharField(max_length=50, blank=True)
    payment_terms_days = models.IntegerField(default=30)
    bank_account_iban = models.CharField(max_length=34, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_finance_ap_vendors"

    def __str__(self):
        return f"{self.vendor_code} - {self.name}"


class Bill(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("partial", "Partial"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name="bills"
    )
    bill_number = models.CharField(max_length=50)
    bill_date = models.DateField()
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    class Meta:
        db_table = "cycom_finance_ap_bills"

    def __str__(self):
        return f"{self.bill_number} - {self.vendor}"


class BillLine(BaseModel):
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name="lines"
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_finance_ap_bill_lines"

    def __str__(self):
        return f"Line {self.id} - {self.description[:50]}"


class VendorPayment(BaseModel):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name="payments"
    )
    bill = models.ForeignKey(
        Bill,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    method = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cycom_finance_ap_vendor_payments"

    def __str__(self):
        return f"Payment {self.id} - {self.vendor} ({self.amount})"
