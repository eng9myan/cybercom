from django.db import models

from platform.common.models import BaseModel


class DeploymentProfile(BaseModel):
    """Deployment profile defines how and where CyMed is deployed."""

    PROFILE_TYPES = [
        ("saas", "SaaS (CyMed Cloud)"),
        ("private_cloud", "Private Cloud"),
        ("government_cloud", "Government Cloud"),
        ("hybrid", "Hybrid"),
        ("air_gapped", "Air-Gapped"),
    ]

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    profile_type = models.CharField(max_length=50, choices=PROFILE_TYPES)
    description = models.TextField(blank=True)
    requires_offline_license = models.BooleanField(default=False)
    supports_auto_update = models.BooleanField(default=True)
    supports_telemetry = models.BooleanField(default=True)
    requires_government_clearance = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_commercial_deployment_profiles"

    def __str__(self):
        return f"{self.code} ({self.profile_type})"


class DeploymentConfiguration(BaseModel):
    """Per-customer deployment configuration bound to a profile."""

    profile = models.ForeignKey(
        DeploymentProfile, on_delete=models.PROTECT, related_name="configurations"
    )
    customer_id = models.UUIDField()
    configuration_name = models.CharField(max_length=255)

    # Infrastructure
    cloud_provider = models.CharField(max_length=100, blank=True)  # AWS, Azure, GCP, On-prem
    region = models.CharField(max_length=100, blank=True)
    cluster_name = models.CharField(max_length=255, blank=True)
    database_host = models.CharField(max_length=500, blank=True)

    # Network
    is_internet_accessible = models.BooleanField(default=True)
    vpn_required = models.BooleanField(default=False)
    ip_whitelist = models.JSONField(default=list, blank=True)

    # Update policy
    update_channel = models.CharField(max_length=50, default="stable")  # stable, lts, edge
    maintenance_window = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_commercial_deployment_configurations"


class DeploymentCapability(BaseModel):
    """Defines what capabilities are available in a given deployment profile."""

    profile = models.ForeignKey(
        DeploymentProfile, on_delete=models.CASCADE, related_name="capabilities"
    )
    capability_code = models.CharField(
        max_length=200
    )  # "online_activation", "auto_update", "telemetry"
    is_supported = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_commercial_deployment_capabilities"
        unique_together = [("profile", "capability_code")]
