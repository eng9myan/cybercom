"""
Custom-fields tests.

Values are never stored in their own table -- they live on the target
record's own `attributes` JSONField (platform.common.models.AttributesMixin),
so the tests that matter most here are: the whitelist can't be escaped to an
arbitrary model, an unknown/inactive field_key is rejected rather than
silently written, type validation actually rejects the wrong shape, and a
saved value really persists on the underlying record (not just in the
response echo).
"""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.catalog.models import Product
from products.cycom.customfields.models import CustomFieldDefinition

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "ops@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["tenant_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _product(tenant_id, **kw):
    defaults = dict(tenant_id=tenant_id, name="Widget", internal_ref=f"W-{uuid.uuid4().hex[:8]}", product_type="STORABLE")
    defaults.update(kw)
    return Product.objects.create(**defaults)


def _definition(admin_client, **overrides):
    payload = dict(model_key="product", field_key="warranty_months", label="Warranty (months)", field_type="number")
    payload.update(overrides)
    return admin_client.post("/api/v1/customfields/definitions/", payload, format="json")


def test_definitions_list_returns_a_bare_array_not_a_paginated_envelope(admin_client):
    # The project-wide default PageNumberPagination would silently wrap this
    # in {"count", "next", "previous", "results"} -- the settings UI calls
    # `.map()` straight on the response and breaks if it ever regresses.
    _definition(admin_client)
    resp = admin_client.get("/api/v1/customfields/definitions/?model_key=product")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)


def test_registry_lists_the_whitelisted_models(admin_client):
    resp = admin_client.get("/api/v1/customfields/registry/")
    assert resp.status_code == 200
    keys = {row["key"] for row in resp.data}
    assert "product" in keys
    assert "employee" in keys


def test_definition_rejects_a_model_key_outside_the_whitelist(admin_client):
    resp = _definition(admin_client, model_key="ir.model.fields")
    assert resp.status_code == 400
    assert "model_key" in resp.data["detail"]


def test_select_field_requires_at_least_one_option(admin_client):
    resp = _definition(admin_client, field_key="tier", label="Tier", field_type="select", options=[])
    assert resp.status_code == 400
    assert "options" in resp.data["detail"]


def test_field_key_is_immutable_after_creation(admin_client, tenant_id):
    resp = _definition(admin_client)
    defn_id = resp.data["id"]
    patch = admin_client.patch(f"/api/v1/customfields/definitions/{defn_id}/", {"field_key": "renamed"}, format="json")
    assert patch.status_code == 200
    assert patch.data["field_key"] == "warranty_months"  # attempted rename silently ignored, not applied


def test_values_get_merges_definitions_with_unset_record_returning_null(admin_client, tenant_id):
    _definition(admin_client)
    product = _product(tenant_id)
    resp = admin_client.get(f"/api/v1/customfields/values/?model_key=product&record_id={product.id}")
    assert resp.status_code == 200
    assert resp.data[0]["field_key"] == "warranty_months"
    assert resp.data[0]["value"] is None


def test_values_post_persists_onto_the_real_record_attributes(admin_client, tenant_id):
    _definition(admin_client)
    product = _product(tenant_id)
    resp = admin_client.post(
        "/api/v1/customfields/values/",
        {"model_key": "product", "record_id": str(product.id), "values": {"warranty_months": 24}},
        format="json",
    )
    assert resp.status_code == 200
    product.refresh_from_db()
    assert product.attributes["warranty_months"] == 24.0


def test_values_post_rejects_unknown_field_key(admin_client, tenant_id):
    product = _product(tenant_id)
    resp = admin_client.post(
        "/api/v1/customfields/values/",
        {"model_key": "product", "record_id": str(product.id), "values": {"not_a_real_field": "x"}},
        format="json",
    )
    assert resp.status_code == 400
    assert "not_a_real_field" in resp.data["errors"]


def test_values_post_rejects_inactive_field_key(admin_client, tenant_id):
    defn_id = _definition(admin_client).data["id"]
    admin_client.patch(f"/api/v1/customfields/definitions/{defn_id}/", {"is_active": False}, format="json")
    product = _product(tenant_id)
    resp = admin_client.post(
        "/api/v1/customfields/values/",
        {"model_key": "product", "record_id": str(product.id), "values": {"warranty_months": 24}},
        format="json",
    )
    assert resp.status_code == 400
    assert "warranty_months" in resp.data["errors"]


def test_values_post_rejects_wrong_type_for_number(admin_client, tenant_id):
    _definition(admin_client)
    product = _product(tenant_id)
    resp = admin_client.post(
        "/api/v1/customfields/values/",
        {"model_key": "product", "record_id": str(product.id), "values": {"warranty_months": "not a number"}},
        format="json",
    )
    assert resp.status_code == 400
    assert "warranty_months" in resp.data["errors"]


def test_values_post_validates_select_against_its_own_options(admin_client, tenant_id):
    _definition(admin_client, field_key="tier", label="Tier", field_type="select", options=["gold", "silver"])
    product = _product(tenant_id)
    bad = admin_client.post(
        "/api/v1/customfields/values/",
        {"model_key": "product", "record_id": str(product.id), "values": {"tier": "platinum"}},
        format="json",
    )
    assert bad.status_code == 400

    good = admin_client.post(
        "/api/v1/customfields/values/",
        {"model_key": "product", "record_id": str(product.id), "values": {"tier": "gold"}},
        format="json",
    )
    assert good.status_code == 200
    product.refresh_from_db()
    assert product.attributes["tier"] == "gold"


def test_values_post_rejects_empty_required_field(admin_client, tenant_id):
    _definition(admin_client, is_required=True)
    product = _product(tenant_id)
    resp = admin_client.post(
        "/api/v1/customfields/values/",
        {"model_key": "product", "record_id": str(product.id), "values": {"warranty_months": None}},
        format="json",
    )
    assert resp.status_code == 400
    assert "warranty_months" in resp.data["errors"]


def test_values_are_tenant_isolated(admin_client, tenant_id):
    other_tenant = uuid.uuid4()
    other_product = _product(other_tenant)
    resp = admin_client.get(f"/api/v1/customfields/values/?model_key=product&record_id={other_product.id}")
    assert resp.status_code == 404


def test_customfields_endpoints_require_auth():
    anon = APIClient()
    assert anon.get("/api/v1/customfields/registry/").status_code == 401
    assert anon.get("/api/v1/customfields/definitions/").status_code == 401
    assert anon.get("/api/v1/customfields/values/?model_key=product&record_id=x").status_code == 401
