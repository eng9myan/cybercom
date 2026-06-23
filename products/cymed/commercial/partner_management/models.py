from django.db import models
from platform.common.models import BaseModel


class PartnerType(BaseModel):
    """Catalog of partner categories."""
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    commission_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "cymed_commercial_partner_types"

    def __str__(self):
        return self.name


class Partner(BaseModel):
    """CyMed channel partner (reseller, SI, distributor, government)."""
    STATUS_CHOICES = [
        ("prospect", "Prospect"),
        ("onboarding", "Onboarding"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("terminated", "Terminated"),
    ]

    partner_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    partner_type = models.ForeignKey(PartnerType, on_delete=models.PROTECT, related_name="partners")
    country_code = models.CharField(max_length=10)
    regions_covered = models.JSONField(default=list)    # ["JO", "SA", "AE"]
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="prospect")
    partner_level = models.CharField(max_length=50, default="silver")   # silver, gold, platinum

    class Meta:
        db_table = "cymed_commercial_partners"

    def __str__(self):
        return f"{self.partner_number} — {self.name}"


class ResellerAgreement(BaseModel):
    """Reseller agreement with discount tiers and territory rights."""
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name="reseller_agreement")
    agreement_number = models.CharField(max_length=100, unique=True)
    signed_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    territory = models.JSONField(default=list)           # ["JO", "IQ"]
    products_authorized = models.JSONField(default=list) # ["cymed_clinic", "cymed_hospital"]
    discount_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    payment_terms_days = models.PositiveIntegerField(default=30)
    min_annual_commitment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nda_signed = models.BooleanField(default=False)
    can_white_label = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_commercial_reseller_agreements"


class DistributorAgreement(BaseModel):
    """Distributor agreement for regional distribution rights."""
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name="distributor_agreement")
    agreement_number = models.CharField(max_length=100, unique=True)
    signed_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    exclusive_territory = models.JSONField(default=list)   # ["SA"] = exclusive in Saudi Arabia
    sub_reseller_rights = models.BooleanField(default=False)
    localization_rights = models.BooleanField(default=False)
    government_bid_rights = models.BooleanField(default=False)
    annual_volume_commitment = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "cymed_commercial_distributor_agreements"
