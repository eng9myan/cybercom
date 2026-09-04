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
def test_emit_domain_event_and_relay():
    from io import StringIO

    from django.core.management import call_command

    from platform.canonical.events import emit, unpublished

    tid = uuid.uuid4()
    agg = uuid.uuid4()
    with tenant_context(tid):
        e = emit(
            event_type="order.placed", aggregate_type="Order", aggregate_id=agg,
            payload={"total": 10}, tenant_id=tid,
        )
        assert e.published_at is None
        assert unpublished().filter(pk=e.pk).exists()

        call_command("relay_domain_events", "--dry-run", stdout=StringIO())
        e.refresh_from_db()
        assert e.published_at is None  # dry run

        call_command("relay_domain_events", stdout=StringIO())
        e.refresh_from_db()
        assert e.published_at is not None
        assert not unpublished().filter(pk=e.pk).exists()


@pytest.fixture
def _isolated_handlers():
    from platform.canonical import events as ev

    saved = list(ev._HANDLERS)
    ev._HANDLERS.clear()
    yield ev._HANDLERS
    ev._HANDLERS[:] = saved


@pytest.mark.django_db
def test_relay_dispatches_to_in_process_handlers(_isolated_handlers):
    from platform.canonical import events as ev

    seen = []
    _isolated_handlers.append(("cymed.patient.*", lambda e: seen.append(e.event_type)))
    _isolated_handlers.append(("*", lambda e: seen.append("ALL:" + e.event_type)))

    tid = uuid.uuid4()
    with tenant_context(tid):
        ev.emit(event_type="cymed.patient.merged", aggregate_type="Patient",
                aggregate_id=uuid.uuid4(), tenant_id=tid)
        ev.emit(event_type="cycom.invoice.posted", aggregate_type="Invoice",
                aggregate_id=uuid.uuid4(), tenant_id=tid)
    ev.relay()

    assert "cymed.patient.merged" in seen            # prefix match
    assert "ALL:cymed.patient.merged" in seen         # wildcard match
    assert "ALL:cycom.invoice.posted" in seen
    assert "cycom.invoice.posted" not in seen         # prefix must not over-match


@pytest.mark.django_db
def test_a_failing_handler_does_not_stall_the_relay(_isolated_handlers):
    from platform.canonical import events as ev

    def boom(e):
        raise RuntimeError("nope")

    hits = []
    _isolated_handlers.append(("*", boom))
    _isolated_handlers.append(("*", lambda e: hits.append(e.event_type)))

    tid = uuid.uuid4()
    with tenant_context(tid):
        e = ev.emit(event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
                    tenant_id=tid)
    sent = ev.relay()
    assert sent == 1
    assert hits == ["x"]
    e.refresh_from_db()
    assert e.published_at is not None


@pytest.mark.django_db
def test_relay_domain_events_celery_task():
    from platform.canonical.events import emit, unpublished
    from platform.canonical.tasks import relay_domain_events

    tid = uuid.uuid4()
    with tenant_context(tid):
        emit(event_type="x", aggregate_type="X", aggregate_id=uuid.uuid4(),
             tenant_id=tid)
        emit(event_type="y", aggregate_type="Y", aggregate_id=uuid.uuid4(),
             tenant_id=tid)
    sent = relay_domain_events.apply().get()  # eager
    assert sent == 2
    assert not unpublished().exists()


@pytest.mark.django_db
def test_consent_grant_gates_cross_tenant_access():
    from platform.canonical.consent import ConsentDenied, has_consent, require_consent

    grantor, grantee = uuid.uuid4(), uuid.uuid4()

    # no grant -> denied
    assert has_consent(grantor, grantee_tenant_id=grantee, entity="Referral",
                       purpose="care_coordination") is False
    with pytest.raises(ConsentDenied):
        require_consent(grantor, grantee_tenant_id=grantee, entity="Referral",
                        purpose="care_coordination")

    with tenant_context(grantor):
        ConsentGrant.objects.create(
            tenant_id=grantor, grantee_tenant_id=grantee,
            scope={"entities": ["Referral"], "purpose": "care_coordination"},
        )

    # covered scope -> allowed
    assert has_consent(grantor, grantee_tenant_id=grantee, entity="Referral",
                       purpose="care_coordination") is True
    # wrong entity / purpose -> still denied
    assert has_consent(grantor, grantee_tenant_id=grantee, entity="Invoice",
                       purpose="care_coordination") is False
    assert has_consent(grantor, grantee_tenant_id=grantee, entity="Referral",
                       purpose="marketing") is False
    # wrong grantee -> denied
    assert has_consent(grantor, grantee_tenant_id=uuid.uuid4(), entity="Referral",
                       purpose="care_coordination") is False


@pytest.mark.django_db
def test_consent_grant_expiry_is_respected():
    from django.utils import timezone

    from platform.canonical.consent import has_consent

    grantor, grantee = uuid.uuid4(), uuid.uuid4()
    with tenant_context(grantor):
        ConsentGrant.objects.create(
            tenant_id=grantor, grantee_tenant_id=grantee, scope={},
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
    assert has_consent(grantor, grantee_tenant_id=grantee) is False


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
