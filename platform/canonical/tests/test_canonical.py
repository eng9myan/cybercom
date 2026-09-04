"""M1 canonical model smoke tests + the BaseModel mixin behaviour."""

import uuid

import pytest

from platform.canonical.models import (
    ConsentGrant,
    ConsentGrantStatus,
    DomainEvent,
    FxRate,
    LayoutTemplate,
    VerticalFlavor,
)
from platform.common.actor_context import actor_context, get_current_actor
from platform.common.tenant_context import tenant_context


@pytest.mark.django_db
def test_platform_flavor_and_layout_and_fx_round_trip():
    vf = VerticalFlavor.objects.create(key="retail", name="Retail", version="1.0.0")
    assert vf.status == "engine_only"

    lt = LayoutTemplate.objects.create(
        flavor_key="retail", name="POS home", route="/pos", device="pos",
        slots={"header": "ds.AppBar"},
    )
    assert lt.slots["header"] == "ds.AppBar"

    fx = FxRate.objects.create(
        base_currency="USD", quote_currency="JOD", rate="0.709", as_of="2026-09-01",
    )
    fx.refresh_from_db()
    assert str(fx.rate) == "0.70900000"  # DecimalField(decimal_places=8) quantises


@pytest.mark.django_db
def test_consent_grant_is_tenant_scoped_and_effective():
    tid = uuid.uuid4()
    with tenant_context(tid):
        g = ConsentGrant.objects.create(
            tenant_id=tid,
            grantee_tenant_id=uuid.uuid4(),
            scope={"entities": ["Order"], "purpose": "analytics"},
        )
        assert g.tenant_id == tid
        assert g.is_effective() is True
        g.status = ConsentGrantStatus.REVOKED
        assert g.is_effective() is False


@pytest.mark.django_db
def test_domain_event_outbox_defaults():
    tid = uuid.uuid4()
    with tenant_context(tid):
        e = DomainEvent.objects.create(
            tenant_id=tid,
            event_type="order.placed",
            aggregate_type="Order",
            aggregate_id=uuid.uuid4(),
            payload={"total": 10},
        )
        assert e.published_at is None
        assert e.attempts == 0
        assert e.schema_version == 1


@pytest.mark.django_db
def test_basemodel_row_version_bumps_on_every_save():
    tid = uuid.uuid4()
    with tenant_context(tid):
        e = DomainEvent.objects.create(
            tenant_id=tid, event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
        )
        assert e.row_version == 1
        e.attempts = 1
        e.save(update_fields=["attempts"])
        e.refresh_from_db()
        assert e.row_version == 2  # bumped + persisted despite a targeted update_fields


@pytest.mark.django_db
def test_basemodel_has_attributes_and_actor_columns():
    tid = uuid.uuid4()
    with tenant_context(tid):
        e = DomainEvent.objects.create(
            tenant_id=tid, event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
            attributes={"k": "v"}, created_by=uuid.uuid4(),
        )
        e.refresh_from_db()
        assert e.attributes == {"k": "v"}
        # explicit created_by= wins over the (unset) actor context
        assert e.created_by is not None


@pytest.mark.django_db
def test_actor_context_fills_created_by_and_updated_by():
    tid, actor = uuid.uuid4(), uuid.uuid4()
    with tenant_context(tid), actor_context(actor):
        e = DomainEvent.objects.create(
            tenant_id=tid, event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
        )
        e.refresh_from_db()
        assert e.created_by == actor
        assert e.updated_by == actor

    # a second actor updating the row: created_by stays, updated_by moves
    actor2 = uuid.uuid4()
    with tenant_context(tid), actor_context(actor2):
        e.attempts = 5
        e.save(update_fields=["attempts"])
    e.refresh_from_db()
    assert e.created_by == actor
    assert e.updated_by == actor2  # persisted despite the targeted update_fields


@pytest.mark.django_db
def test_no_actor_context_leaves_columns_null():
    tid = uuid.uuid4()
    with tenant_context(tid):
        e = DomainEvent.objects.create(
            tenant_id=tid, event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
        )
        e.refresh_from_db()
        assert e.created_by is None
        assert e.updated_by is None


def test_actor_context_coerces_and_isolates():
    assert get_current_actor() is None
    with actor_context("not-a-uuid"):
        assert get_current_actor() is None  # malformed sub -> None, never raises
    u = uuid.uuid4()
    with actor_context(str(u)):
        assert get_current_actor() == u
    assert get_current_actor() is None  # reset on exit


@pytest.mark.django_db
def test_save_if_unchanged_compare_and_set():
    from platform.common.models import OptimisticLockError

    tid = uuid.uuid4()
    with tenant_context(tid):
        e = DomainEvent.objects.create(
            tenant_id=tid, event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
        )
        rv0 = e.row_version

        # a concurrent writer bumps the row out from under us
        other = DomainEvent.objects.get(pk=e.pk)
        other.attempts = 99
        other.save(update_fields=["attempts"])

        e.attempts = 1
        with pytest.raises(OptimisticLockError):
            e.save_if_unchanged(fields=["attempts"])

        # reload, retry, succeeds and advances the local row_version
        e.refresh_from_db()
        e.attempts = 2
        e.save_if_unchanged(fields=["attempts"])
        assert e.row_version > rv0
        e.refresh_from_db()
        assert e.attempts == 2


@pytest.mark.django_db
def test_backfill_audit_columns_command():
    from io import StringIO

    from django.core.management import call_command

    tid, creator = uuid.uuid4(), uuid.uuid4()
    with tenant_context(tid):
        # a row created by someone, never updated by a distinct actor, row_version 0
        e = DomainEvent.objects.create(
            tenant_id=tid, event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
        )
        DomainEvent.objects.filter(pk=e.pk).update(
            row_version=0, created_by=creator, updated_by=None,
        )

    out = StringIO()
    call_command("backfill_audit_columns", "--dry-run", stdout=out)
    assert "would set" in out.getvalue()

    e.refresh_from_db()
    assert e.row_version == 0  # dry run changed nothing

    call_command("backfill_audit_columns", stdout=StringIO())
    e.refresh_from_db()
    assert e.row_version == 1          # 0 -> 1
    assert e.updated_by == creator     # NULL -> created_by
    assert e.created_by == creator     # untouched
