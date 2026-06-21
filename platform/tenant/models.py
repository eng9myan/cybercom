"""
Tenant registry model. ADR-0002: tiered multi-tenancy.
Tenants are registered here; isolation enforced via PostgreSQL RLS.
"""
import uuid
from django.db import models
from django.utils import timezone
from platform.common.models import PlatformModel


class TenantTier(models.TextChoices):
    SHARED = "shared", "Shared (RLS)"
    SCHEMA = "schema", "Schema-per-Tenant"
    DATABASE = "database", "Database-per-Tenant"
    CLUSTER = "cluster", "Cluster-per-Tenant (Sovereign)"


class TenantStatus(models.TextChoices):
    PENDING = "pending", "Pending Activation"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    TERMINATED = "terminated", "Terminated"


class Tenant(PlatformModel):
    """
    Central registry of all tenants on the CyberCom platform.
    One row per organization. platform.tenant.Tenant is the source of truth.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    domain = models.CharField(max_length=253, unique=True, blank=True)
    tier = models.CharField(max_length=20, choices=TenantTier.choices, default=TenantTier.SHARED)
    status = models.CharField(max_length=20, choices=TenantStatus.choices, default=TenantStatus.PENDING)
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    country_code = models.CharField(max_length=2, default="SA")
    timezone = models.CharField(max_length=50, default="Asia/Riyadh")
    locale = models.CharField(max_length=10, default="ar")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_tenants"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"

    def activate(self) -> None:
        self.status = TenantStatus.ACTIVE
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "activated_at", "updated_at"])

    def suspend(self) -> None:
        self.status = TenantStatus.SUSPENDED
        self.suspended_at = timezone.now()
        self.save(update_fields=["status", "suspended_at", "updated_at"])
