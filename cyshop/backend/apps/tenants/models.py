from django.db import models
from django.conf import settings
import uuid
import time
import os

def generate_uuid7():
    try:
        import uuid6
        return uuid6.uuid7()
    except ImportError:
        ms = int(time.time() * 1000)
        byte_array = bytearray(16)
        byte_array[0:6] = ms.to_bytes(6, byteorder='big')
        seq_val = int.from_bytes(os.urandom(2), byteorder='big') & 0x0FFF
        byte_array[6:8] = (0x7000 | seq_val).to_bytes(2, byteorder='big')
        rand_val = int.from_bytes(os.urandom(8), byteorder='big') & 0x3FFFFFFFFFFFFFFF
        byte_array[8:16] = (0x8000000000000000 | rand_val).to_bytes(8, byteorder='big')
        return uuid.UUID(bytes=bytes(byte_array))

class BaseEntity(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    version = models.IntegerField(default=1)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            self.version += 1
        super().save(*args, **kwargs)

class Tenant(BaseEntity):
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class TenantSettings(BaseEntity):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='settings')
    logo_url = models.URLField(max_length=500, null=True, blank=True)
    theme_mode = models.CharField(max_length=20, default='DARK') # LIGHT, DARK, SYSTEM
    primary_color = models.CharField(max_length=7, default='#ED6C00')
    currency = models.CharField(max_length=3, default='JOD')
    timezone = models.CharField(max_length=100, default='Asia/Amman')
    language = models.CharField(max_length=10, default='ar') # ar, en
    subscription_tier = models.CharField(max_length=50, default='STARTER') # STARTER, GROWTH, BUSINESS, ENTERPRISE
    subscription_status = models.CharField(max_length=50, default='ACTIVE') # ACTIVE, SUSPENDED, TRIAL
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Settings for {self.tenant.name}"

class MarketplaceStatus(models.TextChoices):
    NOT_APPLIED = 'not_applied', 'Not Applied'
    APPLICATION_PENDING = 'application_pending', 'Application Pending'
    DOCUMENTS_REQUIRED = 'documents_required', 'Documents Required'
    COMPLIANCE_REVIEW = 'compliance_review', 'Compliance Review'
    APPROVED = 'approved', 'Approved'
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    REJECTED = 'rejected', 'Rejected'
    TERMINATED = 'terminated', 'Terminated'


class MerchantVerificationStatus(models.TextChoices):
    UNVERIFIED = 'unverified', 'Unverified'
    PENDING = 'pending', 'Pending'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'


class Company(BaseEntity):
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True, blank=True)
    tax_number = models.CharField(max_length=100, null=True, blank=True)
    country_code = models.CharField(max_length=2, default='JO') # JO, SA, AE

    # CyMart marketplace eligibility (CyberCom master spec section 7).
    # CyShop companies are inherently customer-facing retail/F&B businesses,
    # so this defaults True here — it matters more for CyCom, where most
    # companies are not customer-facing and must NOT default to eligible.
    operates_customer_facing_store = models.BooleanField(default=True)
    marketplace_eligible = models.BooleanField(default=False)
    marketplace_agreement_signed = models.BooleanField(default=False)
    marketplace_agreement_signed_at = models.DateTimeField(null=True, blank=True)
    marketplace_status = models.CharField(
        max_length=32,
        choices=MarketplaceStatus.choices,
        default=MarketplaceStatus.NOT_APPLIED,
    )
    merchant_verification_status = models.CharField(
        max_length=16,
        choices=MerchantVerificationStatus.choices,
        default=MerchantVerificationStatus.UNVERIFIED,
    )

    def __str__(self):
        return self.name

    def sign_marketplace_agreement(self):
        """Records agreement signature. Does not itself grant marketplace_eligible —
        that's a separate compliance-review decision (see marketplace_status)."""
        from django.utils import timezone
        self.marketplace_agreement_signed = True
        self.marketplace_agreement_signed_at = timezone.now()
        if self.marketplace_status == MarketplaceStatus.NOT_APPLIED:
            self.marketplace_status = MarketplaceStatus.APPLICATION_PENDING
        self.save()


class Branch(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    address = models.TextField()
    timezone = models.CharField(max_length=100, default='Asia/Amman')

    # CyMart publication (per-branch — a company may publish only some branches).
    marketplace_enabled = models.BooleanField(default=False)
    # Soft references: CyMart's category taxonomy and commission/settlement/
    # delivery policy models don't exist yet (Phase 3). Real FKs land then.
    marketplace_category_ids = models.JSONField(default=list, blank=True)
    commission_policy_id = models.UUIDField(null=True, blank=True)
    settlement_policy_id = models.UUIDField(null=True, blank=True)
    delivery_policy_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.marketplace_enabled:
            if not self.company.marketplace_agreement_signed:
                raise ValidationError(
                    "Branch cannot be published to CyMart: company has not "
                    "signed the marketplace agreement."
                )
            if self.company.marketplace_status != MarketplaceStatus.ACTIVE:
                raise ValidationError(
                    f"Branch cannot be published to CyMart: company marketplace_status "
                    f"is '{self.company.marketplace_status}', not 'active'."
                )
            if not self.company.operates_customer_facing_store:
                raise ValidationError(
                    "Branch cannot be published to CyMart: company does not "
                    "operate a customer-facing store."
                )

    def save(self, *args, **kwargs):
        # Only the CyMart eligibility rule, not full model validation — avoids
        # changing existing save() behavior for anything unrelated to it.
        self.clean()
        super().save(*args, **kwargs)

class Department(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class WarehousePlaceholder(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class CostCenterPlaceholder(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cost_centers')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"
