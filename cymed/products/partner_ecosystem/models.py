from django.db import models

from platform.common.models import BaseModel

PARTNER_TYPE_CHOICES = [
    ("reseller", "Reseller"),
    ("implementation", "Implementation"),
    ("technology", "Technology"),
    ("isv", "ISV"),
    ("referral", "Referral"),
    ("strategic", "Strategic"),
    ("distributor", "Distributor"),
]

PARTNER_STATUS_CHOICES = [
    ("prospect", "Prospect"),
    ("active", "Active"),
    ("certified", "Certified"),
    ("suspended", "Suspended"),
    ("terminated", "Terminated"),
]

PARTNER_TIER_CHOICES = [
    ("registered", "Registered"),
    ("silver", "Silver"),
    ("gold", "Gold"),
    ("platinum", "Platinum"),
    ("diamond", "Diamond"),
]

APPLICATION_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("under_review", "Under Review"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("on_hold", "On Hold"),
]

CERTIFICATION_TYPE_CHOICES = [
    ("sales", "Sales"),
    ("technical", "Technical"),
    ("implementation", "Implementation"),
    ("architect", "Architect"),
    ("support", "Support"),
]

CERTIFICATION_STATUS_CHOICES = [
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("expired", "Expired"),
    ("revoked", "Revoked"),
]

LEAD_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("converted", "Converted"),
    ("expired", "Expired"),
]

EXTENSION_CATEGORY_CHOICES = [
    ("integration", "Integration"),
    ("analytics", "Analytics"),
    ("workflow", "Workflow"),
    ("ui", "UI"),
    ("ai", "AI"),
    ("compliance", "Compliance"),
    ("reporting", "Reporting"),
]

EXTENSION_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("review", "Review"),
    ("approved", "Approved"),
    ("published", "Published"),
    ("deprecated", "Deprecated"),
]

PRICE_MODEL_CHOICES = [
    ("free", "Free"),
    ("one_time", "One Time"),
    ("subscription", "Subscription"),
    ("usage", "Usage Based"),
]

PORTAL_ACCESS_LEVEL_CHOICES = [
    ("read_only", "Read Only"),
    ("standard", "Standard"),
    ("admin", "Admin"),
]


class Partner(BaseModel):
    class Meta:
        app_label = "cybercom_partners"
        db_table = "cybercom_pe_partner"

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=PARTNER_STATUS_CHOICES, default="prospect")
    country_code = models.CharField(max_length=10, blank=True)
    region = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    tier = models.CharField(max_length=20, choices=PARTNER_TIER_CHOICES, default="registered")
    joined_at = models.DateField(null=True, blank=True)
    contract_expires_at = models.DateField(null=True, blank=True)
    assigned_am_id = models.UUIDField(null=True, blank=True)
    certified_products = models.JSONField(default=list)

    def __str__(self):
        return f"{self.name} ({self.code}) — {self.tier}"


class PartnerApplication(BaseModel):
    class Meta:
        app_label = "cybercom_partners"
        db_table = "cybercom_pe_application"

    partner_name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPE_CHOICES)
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    website = models.URLField(blank=True)
    motivation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default="pending")
    reviewed_by_id = models.UUIDField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Application: {self.partner_name} ({self.status})"


class PartnerCertification(BaseModel):
    class Meta:
        app_label = "cybercom_partners"
        db_table = "cybercom_pe_certification"

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    product_code = models.CharField(max_length=50, db_index=True)
    certification_type = models.CharField(max_length=20, choices=CERTIFICATION_TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=CERTIFICATION_STATUS_CHOICES, default="in_progress"
    )
    issued_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    certificate_url = models.URLField(blank=True)
    certified_consultants = models.PositiveIntegerField(default=0)

    def __str__(self):
        return (
            f"{self.partner.name} — {self.product_code} {self.certification_type} ({self.status})"
        )


class LeadRegistration(BaseModel):
    class Meta:
        app_label = "cybercom_partners"
        db_table = "cybercom_pe_lead_registration"

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="lead_registrations",
    )
    lead_name = models.CharField(max_length=200)
    lead_organization = models.CharField(max_length=200, blank=True)
    lead_email = models.EmailField()
    lead_phone = models.CharField(max_length=50, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    opportunity_description = models.TextField(blank=True)
    estimated_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default="pending")
    approved_by_id = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    protected_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Lead: {self.lead_name} — {self.partner.name} ({self.status})"


class MarketplaceExtension(BaseModel):
    class Meta:
        app_label = "cybercom_partners"
        db_table = "cybercom_pe_marketplace_extension"

    partner = models.ForeignKey(
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marketplace_extensions",
    )
    extension_name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=EXTENSION_CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=EXTENSION_STATUS_CHOICES, default="draft")
    price_model = models.CharField(max_length=20, choices=PRICE_MODEL_CHOICES, default="free")
    listing_url = models.URLField(blank=True)
    install_count = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.extension_name} ({self.code}) — {self.status}"


class PartnerPortalAccess(BaseModel):
    class Meta:
        app_label = "cybercom_partners"
        db_table = "cybercom_pe_portal_access"

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="portal_accesses",
    )
    user_id = models.UUIDField(db_index=True)
    access_level = models.CharField(
        max_length=20, choices=PORTAL_ACCESS_LEVEL_CHOICES, default="standard"
    )
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    permissions = models.JSONField(default=list)

    def __str__(self):
        return f"Portal Access: {self.user_id} — {self.partner.name} ({self.access_level})"
