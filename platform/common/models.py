"""
Base model classes for all CyberCom platform models.
Implements ADR-0002 (multi-tenancy via RLS) and ADR-0028 (audit trail).
"""

import uuid

from django.db import models
from django.utils import timezone

from platform.common.tenant_context import TenantContextMissing, get_current_tenant


class UUIDPrimaryKeyMixin(models.Model):
    """All platform entities use UUID primary keys."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    """Automatic created_at / updated_at tracking."""

    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class TenantScopedMixin(models.Model):
    """
    Adds tenant_id to every row. PostgreSQL RLS enforces row-level isolation
    using the `app.current_tenant_id` GUC set by TenantIsolationMiddleware.
    ADR-0002 T-Shared tier.

    On save, if `tenant_id` was not set explicitly it is filled from the ambient
    tenant context (set per request by the middleware, per task by the Celery
    hook). This closes the class of bug where a service calls
    `Model.objects.create(...)` and forgets `tenant_id=` — instead of a bare
    `IntegrityError`, the row gets the right tenant, or a clear
    `TenantContextMissing` if there genuinely is no context.
    See docs/blueprint/specs/canonical-data-model-v1.md §2.2.
    """

    tenant_id = models.UUIDField(db_index=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            tid = get_current_tenant()
            if tid is None:
                raise TenantContextMissing(
                    f"{type(self).__name__}.save() with no tenant_id and no ambient "
                    f"tenant context — pass tenant_id= or wrap in tenant_context(...)."
                )
            self.tenant_id = tid
        super().save(*args, **kwargs)


class SoftDeleteMixin(models.Model):
    """Soft-delete support: records are flagged deleted, not physically removed."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    class Meta:
        abstract = True


class BaseModel(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """
    Standard base model for all tenant-scoped CyberCom entities.
    Inherits: UUID pk, timestamps, tenant isolation.
    """

    class Meta:
        abstract = True


class PlatformModel(UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Base model for platform-level (non-tenant-scoped) entities like
    tenant registry, identity config, system settings.
    """

    class Meta:
        abstract = True
