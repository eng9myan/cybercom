"""Auto Parts — vehicle fitment: reference/search data, never a checkout gate."""

import uuid
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from products.cycom.catalog.models import Product, VehicleFitment


@pytest.fixture
def alternator(db, tenant_id):
    return Product.objects.create(tenant_id=tenant_id, name="Alternator", internal_ref="ALT-1")


@pytest.mark.django_db
def test_matches_within_year_range(tenant_id, alternator):
    fit = VehicleFitment.objects.create(
        tenant_id=tenant_id, product=alternator, make="Toyota", model="Camry",
        year_start=2012, year_end=2017,
    )
    assert fit.matches(make="Toyota", model="Camry", year=2015)
    assert fit.matches(make="toyota", model="CAMRY", year=2012)  # case-insensitive
    assert not fit.matches(make="Toyota", model="Camry", year=2018)
    assert not fit.matches(make="Toyota", model="Corolla", year=2015)


@pytest.mark.django_db
def test_open_ended_year_end_matches_any_later_year(tenant_id, alternator):
    fit = VehicleFitment.objects.create(
        tenant_id=tenant_id, product=alternator, make="Toyota", model="Camry", year_start=2018,
    )
    assert fit.matches(make="Toyota", model="Camry", year=2026)
    assert not fit.matches(make="Toyota", model="Camry", year=2017)


@pytest.mark.django_db
def test_year_end_before_year_start_rejected(tenant_id, alternator):
    with pytest.raises(ValidationError):
        VehicleFitment.objects.create(
            tenant_id=tenant_id, product=alternator, make="Toyota", model="Camry",
            year_start=2018, year_end=2015,
        )


@pytest.mark.django_db
def test_core_charge_field_roundtrips(tenant_id):
    p = Product.objects.create(
        tenant_id=tenant_id, name="Starter Motor", internal_ref="STR-1",
        core_charge=Decimal("25.00"),
    )
    p.refresh_from_db()
    assert p.core_charge == Decimal("25.00")


@pytest.mark.django_db
def test_core_charge_is_optional(tenant_id):
    p = Product.objects.create(tenant_id=tenant_id, name="Wiper Blade", internal_ref="WB-1")
    assert p.core_charge is None


# ── API search ───────────────────────────────────────────────────────────────
@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "admin@cybercom.io",
        "tenant_id": str(tenant_id), "realm_access": {"roles": ["platform_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_fitment_search_endpoint(admin_client, tenant_id, alternator):
    VehicleFitment.objects.create(
        tenant_id=tenant_id, product=alternator, make="Honda", model="Civic",
        year_start=2016, year_end=2021,
    )
    resp = admin_client.get("/api/v1/catalog/vehicle-fitments/search/?make=Honda&model=Civic&year=2019")
    assert resp.status_code == 200, resp.content
    assert len(resp.data) == 1
    assert resp.data[0]["product_name"] == "Alternator"

    resp = admin_client.get("/api/v1/catalog/vehicle-fitments/search/?make=Honda&model=Civic&year=2010")
    assert resp.status_code == 200
    assert len(resp.data) == 0

    resp = admin_client.get("/api/v1/catalog/vehicle-fitments/search/?make=Honda")
    assert resp.status_code == 400
