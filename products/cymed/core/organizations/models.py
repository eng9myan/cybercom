from django.db import models
from platform.common.models import BaseModel

class OrganizationType(models.TextChoices):
    HOSPITAL = "hospital", "Hospital"
    CLINIC = "clinic", "Clinic"
    LABORATORY = "laboratory", "Laboratory"
    IMAGING_CENTER = "imaging_center", "Imaging Center"
    PHARMACY = "pharmacy", "Pharmacy"
    HEALTH_NETWORK = "health_network", "Health Network"

class Organization(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    organization_type = models.CharField(max_length=30, choices=OrganizationType.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_organizations"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.organization_type})"


class OrganizationAddress(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="addresses")
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)

    class Meta:
        db_table = "cymed_organization_addresses"


class OrganizationContact(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="contacts")
    telecom_system = models.CharField(max_length=20, choices=[
        ("phone", "Phone"), ("fax", "Fax"), ("email", "Email"), ("url", "URL")
    ])
    telecom_value = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_organization_contacts"


class OrganizationRelationship(BaseModel):
    source_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="parent_relationships")
    target_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="child_relationships")
    relationship_type = models.CharField(max_length=50, choices=[
        ("parent", "Parent"), ("child", "Child"), ("partner", "Partner")
    ])

    class Meta:
        db_table = "cymed_organization_relationships"
        unique_together = [("source_organization", "target_organization", "relationship_type")]


class OrganizationAccreditation(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="accreditations")
    accreditation_body = models.CharField(max_length=100)  # e.g., "JCI", "Saudi CBAHI"
    accreditation_number = models.CharField(max_length=100)
    valid_until = models.DateField()

    class Meta:
        db_table = "cymed_organization_accreditations"
