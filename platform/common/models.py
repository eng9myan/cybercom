"""
Base model classes for all CyberCom platform models.
Implements ADR-0002 (multi-tenancy via RLS) and ADR-0028 (audit trail).
"""

import uuid

from django.db import models
from django.utils import timezone

from platform.common.actor_context import get_current_actor
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


class AttributesMixin(models.Model):
    """
    Flavor-specific / extension fields (canonical-data-model-v1.md §1.1, §3).
    A vertical flavor declares which keys are valid; the payload is validated
    against the registered profile at the service layer, not by the DB.
    """

    attributes = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True


class OptimisticLockMixin(models.Model):
    """
    `row_version` is bumped on every write. A caller that wants a compare-and-set
    update does `Model.objects.filter(pk=..., row_version=expected).update(...)`
    and checks the affected-row count (canonical-data-model-v1.md §1.2).
    """

    row_version = models.PositiveBigIntegerField(default=0, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.row_version = (self.row_version or 0) + 1
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            uf = set(update_fields)
            if uf:  # a targeted save() must still persist the bump
                uf.add("row_version")
                kwargs["update_fields"] = uf
        super().save(*args, **kwargs)


class BaseModel(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantScopedMixin,
    AttributesMixin,
    OptimisticLockMixin,
):
    """
    Standard base model for all tenant-scoped CyberCom entities.
    Inherits: UUID pk, timestamps, tenant isolation, extension `attributes`,
    optimistic `row_version`, and actor columns (canonical-data-model-v1.md §1.1).
    """

    created_by = models.UUIDField(null=True, editable=False)
    updated_by = models.UUIDField(null=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Fill the audit-actor columns from the ambient actor context
        (canonical-data-model-v1.md §1.2). Best-effort — an unset context or
        an explicit `created_by=`/`updated_by=` on the instance both win."""
        actor = get_current_actor()
        if actor is not None:
            adding = self._state.adding
            touched = []
            if adding and self.created_by is None:
                self.created_by = actor
                touched.append("created_by")
            if self.updated_by != actor:
                self.updated_by = actor
                touched.append("updated_by")

            update_fields = kwargs.get("update_fields")
            if update_fields is not None and touched:
                uf = set(update_fields)
                if uf:
                    uf.update(touched)
                    kwargs["update_fields"] = uf

        super().save(*args, **kwargs)


class PlatformModel(UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Base model for platform-level (non-tenant-scoped) entities like
    tenant registry, identity config, system settings.
    """

    class Meta:
        abstract = True
