from django.db import models
from platform.common.models import BaseModel


DEPLOYMENT_TYPE_CHOICES = [
    ("cloud", "Cloud (SaaS)"),
    ("private_cloud", "Private Cloud"),
    ("government_cloud", "Government Cloud"),
    ("on_premises", "On-Premises"),
    ("hybrid", "Hybrid"),
    ("air_gapped", "Air-Gapped"),
]

TENANCY_MODEL_CHOICES = [
    ("single_tenant", "Single Tenant"),
    ("multi_tenant", "Multi-Tenant"),
]

INFRASTRUCTURE_CHOICES = [
    ("kubernetes", "Kubernetes"),
    ("docker_compose", "Docker Compose"),
    ("aws_ecs", "AWS ECS"),
    ("aws_eks", "AWS EKS"),
    ("azure_aks", "Azure AKS"),
    ("gcp_gke", "GCP GKE"),
    ("oracle_oke", "Oracle OKE"),
    ("vmware", "VMware vSphere"),
    ("bare_metal", "Bare Metal"),
]

DEPLOYMENT_STATUS_CHOICES = [
    ("planned", "Planned"),
    ("validating", "Validating Environment"),
    ("provisioning", "Provisioning"),
    ("installing", "Installing"),
    ("configuring", "Configuring"),
    ("testing", "Testing"),
    ("go_live", "Go-Live"),
    ("live", "Live"),
    ("maintenance", "Maintenance"),
    ("decommissioned", "Decommissioned"),
    ("failed", "Failed"),
]

HEALTH_STATUS_CHOICES = [
    ("healthy", "Healthy"),
    ("degraded", "Degraded"),
    ("critical", "Critical"),
    ("unknown", "Unknown"),
]


class DeploymentRecord(BaseModel):
    class Meta:
        app_label = "cybercom_deployment"
        db_table = "cybercom_deploy_record"

    customer_id = models.UUIDField(db_index=True)
    customer_name = models.CharField(max_length=200)
    deployment_code = models.CharField(max_length=50, unique=True)
    deployment_type = models.CharField(max_length=30, choices=DEPLOYMENT_TYPE_CHOICES)
    tenancy_model = models.CharField(max_length=20, choices=TENANCY_MODEL_CHOICES, default="single_tenant")
    infrastructure = models.CharField(max_length=30, choices=INFRASTRUCTURE_CHOICES)
    status = models.CharField(max_length=20, choices=DEPLOYMENT_STATUS_CHOICES, default="planned")
    region = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    platform_version = models.CharField(max_length=50, blank=True)
    licensed_products = models.JSONField(default=list)
    go_live_date = models.DateField(null=True, blank=True)
    assigned_engineer_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer_name} — {self.deployment_code} ({self.status})"


class EnvironmentCheck(BaseModel):
    class Meta:
        app_label = "cybercom_deployment"
        db_table = "cybercom_deploy_env_check"

    deployment = models.ForeignKey(
        DeploymentRecord,
        on_delete=models.CASCADE,
        related_name="environment_checks",
    )
    check_name = models.CharField(max_length=200)
    check_category = models.CharField(max_length=50)
    passed = models.BooleanField(default=False)
    detail = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.check_name}: {'PASS' if self.passed else 'FAIL'}"


class DeploymentStep(BaseModel):
    class Meta:
        app_label = "cybercom_deployment"
        db_table = "cybercom_deploy_step"
        ordering = ["step_order"]

    deployment = models.ForeignKey(
        DeploymentRecord,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    step_order = models.PositiveSmallIntegerField()
    step_name = models.CharField(max_length=200)
    step_category = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed"), ("failed", "Failed"), ("skipped", "Skipped")],
        default="pending",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    output_log = models.TextField(blank=True)
    error_detail = models.TextField(blank=True)

    def __str__(self):
        return f"Step {self.step_order}: {self.step_name} ({self.status})"


class TenantProvision(BaseModel):
    class Meta:
        app_label = "cybercom_deployment"
        db_table = "cybercom_deploy_tenant_provision"

    deployment = models.ForeignKey(
        DeploymentRecord,
        on_delete=models.CASCADE,
        related_name="tenant_provisions",
    )
    tenant_name = models.CharField(max_length=200)
    tenant_slug = models.CharField(max_length=100)
    platform_tenant_id = models.UUIDField(null=True, blank=True)
    admin_email = models.EmailField()
    edition = models.CharField(max_length=50)
    country_config = models.CharField(max_length=10, default="USA")
    language_code = models.CharField(max_length=10, default="en")
    provisioned_at = models.DateTimeField(null=True, blank=True)
    license_key = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("provisioned", "Provisioned"), ("failed", "Failed")],
        default="pending",
    )

    def __str__(self):
        return f"Provision: {self.tenant_slug} ({self.status})"


class BackupRecord(BaseModel):
    class Meta:
        app_label = "cybercom_deployment"
        db_table = "cybercom_deploy_backup"

    deployment = models.ForeignKey(
        DeploymentRecord,
        on_delete=models.CASCADE,
        related_name="backups",
    )
    backup_type = models.CharField(
        max_length=20,
        choices=[("full", "Full"), ("incremental", "Incremental"), ("snapshot", "Snapshot")],
    )
    storage_location = models.CharField(max_length=500)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed"), ("failed", "Failed")],
        default="pending",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    retention_days = models.PositiveSmallIntegerField(default=30)
    expires_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Backup {self.backup_type} for {self.deployment.deployment_code} ({self.status})"


class HealthCheckSnapshot(BaseModel):
    class Meta:
        app_label = "cybercom_deployment"
        db_table = "cybercom_deploy_health_snapshot"

    deployment = models.ForeignKey(
        DeploymentRecord,
        on_delete=models.CASCADE,
        related_name="health_snapshots",
    )
    overall_status = models.CharField(max_length=20, choices=HEALTH_STATUS_CHOICES, default="unknown")
    component_statuses = models.JSONField(default=dict)
    checked_at = models.DateTimeField(auto_now_add=True)
    uptime_seconds = models.BigIntegerField(null=True, blank=True)
    error_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Health {self.overall_status} — {self.deployment.deployment_code}"


class UpgradeRecord(BaseModel):
    class Meta:
        app_label = "cybercom_deployment"
        db_table = "cybercom_deploy_upgrade"

    deployment = models.ForeignKey(
        DeploymentRecord,
        on_delete=models.CASCADE,
        related_name="upgrades",
    )
    from_version = models.CharField(max_length=50)
    to_version = models.CharField(max_length=50)
    upgrade_type = models.CharField(
        max_length=20,
        choices=[("patch", "Patch"), ("minor", "Minor"), ("major", "Major")],
    )
    status = models.CharField(
        max_length=20,
        choices=[("scheduled", "Scheduled"), ("in_progress", "In Progress"), ("completed", "Completed"), ("rolled_back", "Rolled Back"), ("failed", "Failed")],
        default="scheduled",
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    rollback_available = models.BooleanField(default=True)
    upgrade_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Upgrade {self.from_version} -> {self.to_version} ({self.status})"
