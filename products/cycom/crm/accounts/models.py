from django.db import models

from platform.common.models import BaseModel


class CRMAccount(BaseModel):
    ACCOUNT_TYPE_CHOICES = [
        ("hospital", "Hospital"),
        ("clinic", "Clinic"),
        ("insurance", "Insurance"),
        ("government", "Government"),
        ("corporate", "Corporate"),
    ]
    STATUS_CHOICES = [
        ("prospect", "Prospect"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("churned", "Churned"),
    ]

    account_number = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    industry = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=254, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    assigned_to_id = models.UUIDField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="prospect")

    class Meta:
        db_table = "cycom_crm_accounts"


class AccountContact(BaseModel):
    account = models.ForeignKey(CRMAccount, on_delete=models.CASCADE, related_name="contacts")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=254, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_crm_account_contacts"
