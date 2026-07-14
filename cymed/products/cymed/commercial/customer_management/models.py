from django.db import models

from platform.common.models import BaseModel


class Customer(BaseModel):
    """Master customer record — a healthcare organization buying CyMed."""

    CUSTOMER_TYPES = [
        ("clinic", "Clinic / Medical Center"),
        ("hospital", "Hospital"),
        ("hospital_group", "Hospital Group"),
        ("ministry", "Ministry of Health"),
        ("government", "Government Agency"),
        ("network", "Healthcare Network"),
        ("laboratory", "Laboratory"),
        ("imaging_center", "Imaging Center"),
        ("pharmacy_chain", "Pharmacy Chain"),
    ]
    STATUS_CHOICES = [
        ("lead", "Lead"),
        ("prospect", "Prospect"),
        ("active", "Active Customer"),
        ("churned", "Churned"),
        ("suspended", "Suspended"),
    ]

    # Identity
    customer_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=50, choices=CUSTOMER_TYPES)
    country_code = models.CharField(max_length=10)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    # Licensing identity
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="prospect")
    csm_id = models.UUIDField(null=True, blank=True)  # Customer Success Manager

    class Meta:
        db_table = "cymed_commercial_customers"

    def __str__(self):
        return f"{self.customer_number} — {self.name}"


class CustomerOrganization(BaseModel):
    """Links a Customer to one or more CyMed tenant organizations."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="organizations")
    organization_name = models.CharField(max_length=255)
    organization_code = models.CharField(max_length=100)
    primary_contact_name = models.CharField(max_length=255, blank=True)
    primary_contact_email = models.EmailField(blank=True)
    primary_contact_phone = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "cymed_commercial_customer_organizations"


class CustomerContract(BaseModel):
    """Formal contract between CyMed and a customer."""

    CONTRACT_TYPES = [
        ("saas", "SaaS Agreement"),
        ("enterprise", "Enterprise License Agreement"),
        ("government", "Government Procurement Contract"),
        ("pilot", "Pilot Agreement"),
        ("reseller", "Reseller Agreement"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("negotiation", "Under Negotiation"),
        ("signed", "Signed"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contracts")
    contract_number = models.CharField(max_length=100, unique=True)
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="draft")
    signed_date = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    payment_schedule = models.JSONField(default=list)
    governing_law = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_commercial_customer_contracts"


class CustomerDeployment(BaseModel):
    """Tracks how and where a customer's CyMed is deployed."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="deployments")
    deployment_profile_code = models.CharField(max_length=100)
    product_code = models.CharField(max_length=100)
    edition_code = models.CharField(max_length=100)
    environment = models.CharField(max_length=50, default="production")  # production, staging, demo
    go_live_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_commercial_customer_deployments"


class CustomerSuccessPlan(BaseModel):
    """Customer success plan with KPIs and milestones."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="success_plans")
    plan_name = models.CharField(max_length=255)
    health_score = models.PositiveSmallIntegerField(default=80)  # 0–100
    nps_score = models.SmallIntegerField(null=True, blank=True)  # -100 to +100
    adoption_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    next_qbr_date = models.DateField(null=True, blank=True)  # Quarterly Business Review
    renewal_risk = models.CharField(max_length=50, default="low")  # low, medium, high
    milestones = models.JSONField(default=list)

    class Meta:
        db_table = "cymed_commercial_customer_success_plans"
