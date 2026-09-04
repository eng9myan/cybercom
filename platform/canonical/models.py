"""
Canonical Data Model v1 — M1 additive tables
(docs/blueprint/specs/canonical-data-model-v1.md §5.1, §6.1).

These land empty at M1. Nothing writes to them yet; the flavor engine (N),
the domain-event relay, and the cross-tenant consent checks fill them in
Phase-1 follow-ups. Additive-only: no existing table is touched.
"""
import uuid

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel, PlatformModel


# ── Platform-scoped (P) ────────────────────────────────────────────────────
class VerticalFlavorStatus(models.TextChoices):
    ENGINE_ONLY = "engine_only", "Engine-only"
    COMMUNITY = "community", "Community"
    VERIFIED = "verified", "Verified"
    CERTIFIED = "certified", "Certified"
    GA = "ga", "GA"


class VerticalFlavor(PlatformModel):
    """A registered vertical flavor — the validated `flavor.yaml` (N.1).
    Registry mirrors `schemas/flavor-registry.yaml`."""

    key = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=32, default="0.1.0")  # semver
    definition = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=VerticalFlavorStatus.choices,
        default=VerticalFlavorStatus.ENGINE_ONLY,
    )
    feature_flag = models.CharField(max_length=100, blank=True)
    owner = models.CharField(max_length=200, blank=True)
    certified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform_vertical_flavors"
        ordering = ["key"]

    def __str__(self) -> str:
        return f"{self.key} v{self.version} ({self.status})"


class LayoutTemplate(PlatformModel):
    """A route's slot → design-system-component-id map for a flavor (N.4).
    Component ids only — never raw markup."""

    flavor_key = models.SlugField(max_length=64, db_index=True)
    name = models.CharField(max_length=200)
    route = models.CharField(max_length=255)
    slots = models.JSONField(default=dict, blank=True)
    roles = models.JSONField(default=list, blank=True)
    device = models.CharField(max_length=20, blank=True)  # web | mobile | pos | kiosk

    class Meta:
        db_table = "platform_layout_templates"
        ordering = ["flavor_key", "route"]
        unique_together = [("flavor_key", "route", "device")]

    def __str__(self) -> str:
        return f"{self.flavor_key}:{self.route}"


class FxRate(PlatformModel):
    """Reference FX rate. `rate` is `1 base = <rate> quote`. Financial code
    picks the row with the greatest `as_of <= transaction date`."""

    base_currency = models.CharField(max_length=3)
    quote_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    as_of = models.DateField(db_index=True)
    source = models.CharField(max_length=100, blank=True)  # ecb, central_bank_jo, manual, ...

    class Meta:
        db_table = "platform_fx_rates"
        ordering = ["-as_of"]
        unique_together = [("base_currency", "quote_currency", "as_of", "source")]
        indexes = [models.Index(fields=["base_currency", "quote_currency", "as_of"])]

    def __str__(self) -> str:
        return f"{self.base_currency}/{self.quote_currency} {self.rate} @ {self.as_of}"


# ── Tenant-scoped (T) ─────────────────────────────────────────────────────
class ConsentGrantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class ConsentGrant(BaseModel):
    """The lawful basis for a cross-domain / cross-tenant read (§5.1).
    `tenant_id` = the grantor. Nothing reads another domain's data without a
    matching active grant."""

    grantee_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    grantee_user_id = models.UUIDField(null=True, blank=True, db_index=True)
    scope = models.JSONField(default=dict, blank=True)  # {entities, fields, purpose}
    granted_by = models.UUIDField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=ConsentGrantStatus.choices, default=ConsentGrantStatus.ACTIVE
    )

    class Meta:
        db_table = "core_consent_grants"
        ordering = ["-created_at"]

    def is_effective(self, at=None) -> bool:
        at = at or timezone.now()
        if self.status != ConsentGrantStatus.ACTIVE:
            return False
        return self.expires_at is None or self.expires_at > at


class DomainEvent(BaseModel):
    """Transactional outbox for the canonical domain-event stream (§5.1).
    The relay worker moves rows to the broker; `published_at` stays null until
    then. Distinct from `platform.events.OutboxEvent` (the current relay) —
    canonical consumers migrate onto this in Phase 1."""

    event_type = models.CharField(max_length=200, db_index=True)
    aggregate_type = models.CharField(max_length=100, db_index=True)
    aggregate_id = models.UUIDField(db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    schema_version = models.PositiveSmallIntegerField(default=1)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "core_domain_events"
        ordering = ["occurred_at"]
        indexes = [models.Index(fields=["published_at", "occurred_at"])]

    def __str__(self) -> str:
        return f"{self.event_type} <{self.aggregate_type}:{self.aggregate_id}>"
