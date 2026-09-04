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
        assert e.created_by is not None
        assert e.updated_by is None
