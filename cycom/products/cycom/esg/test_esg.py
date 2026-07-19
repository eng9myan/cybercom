import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.esg.models import EmissionEntry, EmissionFactor


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
def test_entry_computes_co2e_on_save(tenant_id):
    factor = EmissionFactor.objects.create(
        tenant_id=tenant_id, activity_name="Diesel", unit="liter", kg_co2e_per_unit=Decimal("2.680000")
    )
    entry = EmissionEntry.objects.create(
        tenant_id=tenant_id, factor=factor, scope="scope_1",
        quantity=Decimal("100"), activity_date=date.today(),
    )
    assert entry.co2e_kg == Decimal("268.0000")


@pytest.mark.django_db
def test_report_aggregates_by_scope(platform_admin_client, tenant_id):
    diesel = EmissionFactor.objects.create(
        tenant_id=tenant_id, activity_name="Diesel", unit="liter", kg_co2e_per_unit=Decimal("2.68")
    )
    grid = EmissionFactor.objects.create(
        tenant_id=tenant_id, activity_name="Grid Electricity", unit="kWh", kg_co2e_per_unit=Decimal("0.45")
    )
    EmissionEntry.objects.create(
        tenant_id=tenant_id, factor=diesel, scope="scope_1", quantity=Decimal("100"), activity_date=date.today()
    )
    EmissionEntry.objects.create(
        tenant_id=tenant_id, factor=grid, scope="scope_2", quantity=Decimal("1000"), activity_date=date.today()
    )

    resp = platform_admin_client.get("/api/v1/esg/report/")
    assert resp.status_code == 200
    assert Decimal(resp.data["total_co2e_kg"]) == Decimal("268.0000") + Decimal("450.0000")
    assert Decimal(resp.data["by_scope"]["scope_1"]) == Decimal("268.0000")
    assert Decimal(resp.data["by_scope"]["scope_2"]) == Decimal("450.0000")
    assert resp.data["entry_count"] == 2
