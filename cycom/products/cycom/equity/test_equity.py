import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.equity.models import (
    DividendDistribution,
    ShareClass,
    ShareGrant,
    Shareholder,
)


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_waterfall_seniority_and_participation(platform_admin_client, tenant_id):
    common = ShareClass.objects.create(
        tenant_id=tenant_id, name="Common", class_type="common",
    )
    preferred_a = ShareClass.objects.create(
        tenant_id=tenant_id, name="Series A", class_type="preferred",
        liquidation_preference_multiple=Decimal("1.00"), seniority_rank=1, is_participating=False,
    )
    preferred_b = ShareClass.objects.create(
        tenant_id=tenant_id, name="Series B", class_type="preferred",
        liquidation_preference_multiple=Decimal("1.00"), seniority_rank=2, is_participating=True,
    )

    alice = Shareholder.objects.create(tenant_id=tenant_id, name="Alice", holder_type="founder")
    bob = Shareholder.objects.create(tenant_id=tenant_id, name="Bob", holder_type="investor")
    carol = Shareholder.objects.create(tenant_id=tenant_id, name="Carol", holder_type="investor")

    ShareGrant.objects.create(
        tenant_id=tenant_id, shareholder=alice, share_class=common,
        quantity=Decimal("1000"), price_per_share=Decimal("0.001"), grant_date=date.today(),
    )
    ShareGrant.objects.create(
        tenant_id=tenant_id, shareholder=bob, share_class=preferred_a,
        quantity=Decimal("500"), price_per_share=Decimal("2.00"), grant_date=date.today(),
    )
    ShareGrant.objects.create(
        tenant_id=tenant_id, shareholder=carol, share_class=preferred_b,
        quantity=Decimal("200"), price_per_share=Decimal("5.00"), grant_date=date.today(),
    )

    distribution = DividendDistribution.objects.create(
        tenant_id=tenant_id, total_amount=Decimal("5000.00"), distribution_date=date.today(),
    )

    resp = platform_admin_client.post(f"/api/v1/equity/distributions/{distribution.id}/compute/")
    assert resp.status_code == 200, resp.content
    assert resp.data["status"] == "computed"

    # resp.data holds native Python objects (pre-JSON-serialization) -
    # "shareholder" is an actual UUID instance here, not a string.
    totals = {}
    for alloc in resp.data["allocations"]:
        key = str(alloc["shareholder"])
        totals[key] = totals.get(key, Decimal("0")) + Decimal(alloc["amount"])

    assert totals[str(bob.id)] == Decimal("1000.00")  # 500 * 2.00 * 1x preference, non-participating
    assert totals[str(carol.id)] == Decimal("1500.00")  # 1000 preference + 500 pro-rata participation
    assert totals[str(alice.id)] == Decimal("2500.00")  # remaining 3000 pool, 1000/1200 units
    assert sum(totals.values()) == Decimal("5000.00")


@pytest.mark.django_db
def test_vesting_cliff_and_linear(tenant_id):
    shareholder = Shareholder.objects.create(tenant_id=tenant_id, name="Dave", holder_type="employee")
    common = ShareClass.objects.create(tenant_id=tenant_id, name="Common", class_type="common")
    grant = ShareGrant.objects.create(
        tenant_id=tenant_id, shareholder=shareholder, share_class=common,
        quantity=Decimal("4800"), price_per_share=Decimal("0.01"),
        grant_date=date(2024, 1, 1), vesting_start_date=date(2024, 1, 1),
        cliff_months=12, vest_duration_months=48,
    )

    assert grant.vested_quantity(date(2024, 6, 1)) == Decimal("0")  # before cliff
    assert grant.vested_quantity(date(2025, 1, 1)) == Decimal("1200")  # exactly at cliff: 12/48 * 4800
    assert grant.vested_quantity(date(2028, 1, 1)) == Decimal("4800")  # fully vested
