"""
CyberCom Website Public APIs — Domain Models.
Serves cy-com.com marketing content, lead generation, and partner operations.
Public-facing; no tenant scoping on content. Lead capture records include source tenant slug.
"""
import uuid
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ProductCategory(models.TextChoices):
    HEALTHCARE = "healthcare", "Healthcare"
    ERP = "erp", "ERP & Business"
    GOVERNMENT = "government", "Government"
    AI = "ai", "AI Platform"
    IDENTITY = "identity", "Identity & Security"
    INTEGRATION = "integration", "Integration"
    DATA = "data", "Data Platform"
    COMMUNICATIONS = "communications", "Communications"
    CITIZEN = "citizen", "Citizen Services"


class DemoRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONTACTED = "contacted", "Contacted"
    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Demo Completed"
    CLOSED = "closed", "Closed"


class ContactDepartment(models.TextChoices):
    SALES = "sales", "Sales"
    SUPPORT = "support", "Support"
    PARTNERSHIPS = "partnerships", "Partnerships"
    PRESS = "press", "Press & Media"
    CAREERS = "careers", "Careers"
    GENERAL = "general", "General"


class ContactStatus(models.TextChoices):
    NEW = "new", "New"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class PartnerType(models.TextChoices):
    RESELLER = "reseller", "Reseller"
    IMPLEMENTATION = "implementation", "Implementation Partner"
    TECHNOLOGY = "technology", "Technology Partner"
    ISV = "isv", "ISV / Software Partner"
    REFERRAL = "referral", "Referral Partner"
    STRATEGIC = "strategic", "Strategic Alliance"


class PartnerApplicationStatus(models.TextChoices):
    PENDING = "pending", "Pending Review"
    UNDER_REVIEW = "under_review", "Under Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    ON_HOLD = "on_hold", "On Hold"


class DocContentType(models.TextChoices):
    GUIDE = "guide", "Guide"
    REFERENCE = "reference", "API Reference"
    TUTORIAL = "tutorial", "Tutorial"
    RELEASE_NOTE = "release_note", "Release Note"
    FAQ = "faq", "FAQ"
    CHANGELOG = "changelog", "Changelog"


class NewsletterStatus(models.TextChoices):
    PENDING = "pending", "Pending Confirmation"
    ACTIVE = "active", "Active"
    UNSUBSCRIBED = "unsubscribed", "Unsubscribed"
    BOUNCED = "bounced", "Bounced"


# ---------------------------------------------------------------------------
# Public Product Catalog
# ---------------------------------------------------------------------------

class ProductListing(models.Model):
    """
    Public-facing product listings for cy-com.com.
    Separate from the internal commercial product_catalog — this is marketing content.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    tagline = models.CharField(max_length=300, blank=True)
    short_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=ProductCategory.choices, db_index=True)
    parent_product = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_products"
    )
    icon_class = models.CharField(max_length=100, blank=True)
    hero_color = models.CharField(max_length=20, blank=True)
    hero_image_url = models.URLField(blank=True)
    features = models.JSONField(default=list, blank=True)
    key_metrics = models.JSONField(default=list, blank=True)
    editions = models.JSONField(default=list, blank=True)
    compliance_badges = models.JSONField(default=list, blank=True)
    tech_stack = models.JSONField(default=list, blank=True)
    deployment_models = models.JSONField(default=list, blank=True)
    cta_demo_label = models.CharField(max_length=100, default="Request Demo")
    cta_docs_url = models.URLField(blank=True)
    cta_video_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True)
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)
    seo_keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_product_listings"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["category", "is_published"]),
            models.Index(fields=["is_featured", "is_published"]),
        ]

    def __str__(self) -> str:
        return f"ProductListing({self.slug})"


# ---------------------------------------------------------------------------
# Industry Verticals
# ---------------------------------------------------------------------------

class Industry(models.Model):
    """Industry verticals for the website industries section."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    icon_class = models.CharField(max_length=100, blank=True)
    hero_image_url = models.URLField(blank=True)
    challenges = models.JSONField(default=list, blank=True)
    solutions = models.JSONField(default=list, blank=True)
    relevant_products = models.ManyToManyField(ProductListing, blank=True, related_name="industries")
    stats = models.JSONField(default=list, blank=True)
    is_published = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_industries"
        ordering = ["sort_order", "name"]
        verbose_name_plural = "industries"

    def __str__(self) -> str:
        return f"Industry({self.slug})"


# ---------------------------------------------------------------------------
# Case Studies
# ---------------------------------------------------------------------------

class CaseStudy(models.Model):
    """Customer success stories and case studies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=180, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_logo_url = models.URLField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    industry = models.ForeignKey(
        Industry, on_delete=models.SET_NULL, null=True, blank=True, related_name="case_studies"
    )
    products = models.ManyToManyField(ProductListing, blank=True, related_name="case_studies")
    summary = models.TextField(blank=True)
    challenge = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    metrics = models.JSONField(default=list, blank=True)
    quote = models.TextField(blank=True)
    quote_author = models.CharField(max_length=200, blank=True)
    quote_title = models.CharField(max_length=200, blank=True)
    hero_image_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_case_studies"
        ordering = ["-published_at", "-created_at"]
        verbose_name_plural = "case studies"

    def __str__(self) -> str:
        return f"CaseStudy({self.slug})"


# ---------------------------------------------------------------------------
# Demo Request (Lead Generation)
# ---------------------------------------------------------------------------

class DemoRequest(models.Model):
    """
    Inbound demo requests from cy-com.com.
    Routes to CyCom CRM via CyIntegrationHub after creation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=20, unique=True, editable=False)

    # Contact details
    full_name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    company_size = models.CharField(max_length=50, blank=True, choices=[
        ("1-10", "1–10"), ("11-50", "11–50"), ("51-200", "51–200"),
        ("201-1000", "201–1000"), ("1001+", "1001+"),
    ])
    country = models.CharField(max_length=100, blank=True)

    # Request details
    product_interests = models.JSONField(default=list)
    message = models.TextField(blank=True)
    preferred_time = models.CharField(max_length=200, blank=True)
    preferred_date = models.DateField(null=True, blank=True)

    # Attribution
    source = models.CharField(max_length=100, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    referrer_url = models.URLField(blank=True)
    landing_page = models.URLField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # CRM integration
    tenant_slug = models.CharField(max_length=100, blank=True, db_index=True)
    crm_lead_id = models.CharField(max_length=200, blank=True)
    crm_synced_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20, choices=DemoRequestStatus.choices,
        default=DemoRequestStatus.PENDING, db_index=True
    )
    assigned_to = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    gdpr_consent = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_demo_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["email", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"DemoRequest({self.reference_number}, {self.company})"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            import random
            import string
            self.reference_number = "CYB-" + "".join(
                random.choices(string.digits, k=6)
            )
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Contact Message (General Enquiries)
# ---------------------------------------------------------------------------

class ContactMessage(models.Model):
    """General website contact form submissions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)

    full_name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    company = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    department = models.CharField(
        max_length=30, choices=ContactDepartment.choices,
        default=ContactDepartment.GENERAL, db_index=True
    )
    source = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    status = models.CharField(
        max_length=20, choices=ContactStatus.choices,
        default=ContactStatus.NEW, db_index=True
    )
    assigned_to = models.CharField(max_length=200, blank=True)
    response_notes = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    gdpr_consent = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_contact_messages"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ContactMessage({self.ticket_number}, {self.subject[:40]})"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            import random
            import string
            self.ticket_number = "TKT-" + "".join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Partner Application
# ---------------------------------------------------------------------------

class PartnerListing(models.Model):
    """Published partner directory entries."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    logo_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    partner_type = models.CharField(max_length=30, choices=PartnerType.choices, db_index=True)
    expertise_areas = models.JSONField(default=list, blank=True)
    countries = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_partner_listings"
        ordering = ["sort_order", "company_name"]

    def __str__(self) -> str:
        return f"PartnerListing({self.company_name})"


class PartnerApplication(models.Model):
    """Inbound partner program applications from the website."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=20, unique=True, editable=False)

    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    partner_type = models.CharField(max_length=30, choices=PartnerType.choices)
    expertise_areas = models.JSONField(default=list, blank=True)
    years_in_business = models.PositiveSmallIntegerField(null=True, blank=True)
    employee_count = models.CharField(max_length=50, blank=True)
    message = models.TextField(blank=True)
    existing_customers = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=PartnerApplicationStatus.choices,
        default=PartnerApplicationStatus.PENDING, db_index=True
    )
    reviewed_by = models.CharField(max_length=200, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    gdpr_consent = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_partner_applications"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"PartnerApplication({self.reference_number}, {self.company_name})"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            import random
            import string
            self.reference_number = "PAR-" + "".join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

class DocumentationSection(models.Model):
    """Top-level documentation sections (e.g. CyMed / Getting Started)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    product = models.ForeignKey(
        ProductListing, on_delete=models.SET_NULL, null=True, blank=True, related_name="doc_sections"
    )
    icon_class = models.CharField(max_length=100, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_doc_sections"
        ordering = ["sort_order", "title"]

    def __str__(self) -> str:
        return f"DocSection({self.slug})"


class DocumentationItem(models.Model):
    """Individual documentation page or article."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(
        DocumentationSection, on_delete=models.CASCADE, related_name="items"
    )
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=200)
    content_type = models.CharField(max_length=30, choices=DocContentType.choices, db_index=True)
    summary = models.TextField(blank=True)
    content_url = models.URLField(blank=True)
    external_url = models.URLField(blank=True)
    version = models.CharField(max_length=30, blank=True)
    tags = models.JSONField(default=list, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_doc_items"
        ordering = ["sort_order", "title"]
        unique_together = [("section", "slug")]

    def __str__(self) -> str:
        return f"DocItem({self.section.slug}/{self.slug})"


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class NewsletterSubscription(models.Model):
    """Website newsletter sign-ups."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    source = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=NewsletterStatus.choices,
        default=NewsletterStatus.PENDING, db_index=True
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    gdpr_consent = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_newsletter_subscriptions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Newsletter({self.email}, {self.status})"


# ---------------------------------------------------------------------------
# API Audit Log (website-specific, lightweight)
# ---------------------------------------------------------------------------

class WebsiteApiLog(models.Model):
    """
    Lightweight request log for public website API calls.
    Not a security audit — tracks volume, lead sources, and API usage patterns.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    endpoint = models.CharField(max_length=200, db_index=True)
    method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField(db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    response_time_ms = models.PositiveIntegerField(default=0)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)
    was_throttled = models.BooleanField(default=False)
    error_detail = models.TextField(blank=True)

    class Meta:
        db_table = "website_api_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["endpoint", "timestamp"]),
            models.Index(fields=["status_code", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"WebsiteApiLog({self.method} {self.endpoint}, {self.status_code})"

    def save(self, *args, **kwargs):
        if self.pk and WebsiteApiLog.objects.filter(pk=self.pk).exists():
            raise ValueError("WebsiteApiLog records are immutable.")
        super().save(*args, **kwargs)
