"""Flavor engine tests (blueprint N) — registry sync, pack validation,
tenant activation, and the read-only catalog API."""

import uuid
from io import StringIO
from pathlib import Path

import pytest
import yaml
from django.core.management import call_command
from rest_framework.test import APIClient

from platform.canonical import flavors
from platform.canonical.models import LayoutTemplate, VerticalFlavor
from platform.tenant.models import Tenant


@pytest.mark.django_db
def test_sync_registry_loads_full_catalog():
    result = flavors.sync_registry()
    assert result["created"] == result["total"]
    assert result["updated"] == 0
    assert result["total"] == VerticalFlavor.objects.count()

    # spot-check a few well-known entries rather than hardcode the full count,
    # so the registry can grow without breaking this test.
    retail = VerticalFlavor.objects.get(key="retail")
    assert retail.name == "RetailFlavour"
    assert retail.status == "ga"
    assert retail.definition["registry"]["family"] == "commerce"

    hospital = VerticalFlavor.objects.get(key="hospital")
    assert hospital.status == "engine_only"  # hyphen in YAML normalized to underscore
    assert "Ward" in hospital.definition["registry"]["core_plus"]


@pytest.mark.django_db
def test_sync_registry_is_idempotent():
    first = flavors.sync_registry()
    second = flavors.sync_registry()
    assert second["created"] == 0
    assert second["updated"] == first["total"]
    assert VerticalFlavor.objects.count() == first["total"]


@pytest.mark.django_db
def test_sync_registry_matches_yaml_key_set():
    result = flavors.sync_registry()
    data = yaml.safe_load(flavors.DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
    yaml_keys = {e["key"] for entries in data["families"].values() for e in entries}
    assert set(VerticalFlavor.objects.values_list("key", flat=True)) == yaml_keys
    assert result["total"] == len(yaml_keys)


@pytest.mark.django_db
def test_sync_packs_loads_and_validates_retail_pack():
    flavors.sync_registry()
    result = flavors.sync_packs()
    assert "retail" in result["keys"]

    retail = VerticalFlavor.objects.get(key="retail")
    assert retail.version == "0.1.0"
    assert retail.feature_flag == "flavor.retail"
    assert retail.definition["pack"]["flavor"] == "RetailFlavour"
    # the registry metadata from sync_registry() survives the pack merge
    assert retail.definition["registry"]["family"] == "commerce"

    templates = list(LayoutTemplate.objects.filter(flavor_key="retail").order_by("name"))
    assert {t.name for t in templates} == {
        "pos_register", "kds_board", "daily_close", "branch_overview",
    }
    pos = next(t for t in templates if t.name == "pos_register")
    assert pos.slots["cart"] == "ds/order-cart"


@pytest.mark.django_db
def test_sync_packs_is_idempotent_on_layout_templates():
    flavors.sync_packs()
    flavors.sync_packs()
    assert LayoutTemplate.objects.filter(flavor_key="retail").count() == 4


@pytest.mark.django_db
def test_sync_packs_creates_flavor_with_no_registry_entry(tmp_path):
    pack = {
        "flavor": "WidgetFactoryFlavour",
        "version": "0.1.0",
        "modules": ["catalog"],
        "tax_presets": {"countries": [{"country": "SA", "profile": "x"}]},
        "regulatory": [],
    }
    pack_file = tmp_path / "widget.flavor.yaml"
    pack_file.write_text(yaml.safe_dump(pack), encoding="utf-8")

    result = flavors.sync_packs(packs_glob=str(tmp_path / "*.flavor.yaml"))
    assert result["keys"] == ["widget_factory"]
    vf = VerticalFlavor.objects.get(key="widget_factory")
    assert vf.name == "WidgetFactoryFlavour"


@pytest.mark.django_db
def test_sync_packs_rejects_invalid_pack(tmp_path):
    bad_pack = {"flavor": "BrokenFlavour", "version": "0.1.0"}  # missing required fields
    pack_file = tmp_path / "broken.flavor.yaml"
    pack_file.write_text(yaml.safe_dump(bad_pack), encoding="utf-8")

    with pytest.raises(flavors.FlavorValidationError) as exc_info:
        flavors.sync_packs(packs_glob=str(tmp_path / "*.flavor.yaml"))
    assert "broken.flavor.yaml" in str(exc_info.value.path)
    assert exc_info.value.errors  # at least one missing-required-property error

    # a rejected pack must not partially land
    assert not VerticalFlavor.objects.filter(name="BrokenFlavour").exists()


@pytest.mark.django_db
def test_sync_packs_bad_flavor_name_pattern_fails_schema(tmp_path):
    pack = {
        "flavor": "not_pascal_case",  # violates the ^[A-Z]...Flavour$ pattern
        "version": "0.1.0",
        "modules": ["catalog"],
        "tax_presets": {"countries": [{"country": "SA", "profile": "x"}]},
        "regulatory": [],
    }
    pack_file = tmp_path / "bad_name.flavor.yaml"
    pack_file.write_text(yaml.safe_dump(pack), encoding="utf-8")

    with pytest.raises(flavors.FlavorValidationError):
        flavors.sync_packs(packs_glob=str(tmp_path / "*.flavor.yaml"))


@pytest.mark.django_db
def test_get_flavor_and_is_valid_key():
    flavors.sync_registry()
    assert flavors.get_flavor("clinic").name == "ClinicFlavour"
    assert flavors.is_valid_key("clinic") is True
    assert flavors.is_valid_key("no-such-flavor") is False
    with pytest.raises(flavors.FlavorNotFoundError):
        flavors.get_flavor("no-such-flavor")


@pytest.mark.django_db
def test_list_flavors_filters_by_status():
    flavors.sync_registry()
    ga = list(flavors.list_flavors(status="ga"))
    assert {f.key for f in ga} == {"retail", "clinic"}
    assert flavors.list_flavors().count() == VerticalFlavor.objects.count()


@pytest.mark.django_db
def test_enable_and_disable_for_tenant():
    flavors.sync_registry()
    tenant = Tenant.objects.create(name="Acme", slug="acme")
    assert tenant.flavor_set == []

    flavors.enable_for_tenant(tenant, "retail")
    tenant.refresh_from_db()
    assert tenant.flavor_set == ["retail"]

    # idempotent — re-enabling doesn't duplicate
    flavors.enable_for_tenant(tenant, "retail")
    tenant.refresh_from_db()
    assert tenant.flavor_set == ["retail"]

    flavors.enable_for_tenant(tenant, "clinic")
    tenant.refresh_from_db()
    assert set(tenant.flavor_set) == {"retail", "clinic"}

    flavors.disable_for_tenant(tenant, "retail")
    tenant.refresh_from_db()
    assert tenant.flavor_set == ["clinic"]

    # disabling something never enabled (or unregistered) is a safe no-op
    flavors.disable_for_tenant(tenant, "retail")
    flavors.disable_for_tenant(tenant, "no-such-flavor")
    tenant.refresh_from_db()
    assert tenant.flavor_set == ["clinic"]


@pytest.mark.django_db
def test_enable_for_tenant_rejects_unknown_key():
    tenant = Tenant.objects.create(name="Acme2", slug="acme2")
    with pytest.raises(flavors.FlavorNotFoundError):
        flavors.enable_for_tenant(tenant, "no-such-flavor")
    tenant.refresh_from_db()
    assert tenant.flavor_set == []


@pytest.mark.django_db
def test_load_flavor_registry_command():
    out = StringIO()
    call_command("load_flavor_registry", stdout=out)
    output = out.getvalue()
    assert "registry:" in output
    assert "packs:" in output
    assert VerticalFlavor.objects.filter(key="retail").exists()
    assert LayoutTemplate.objects.filter(flavor_key="retail").exists()


@pytest.mark.django_db
def test_load_flavor_registry_command_registry_only():
    out = StringIO()
    call_command("load_flavor_registry", "--registry-only", stdout=out)
    assert "registry:" in out.getvalue()
    assert "packs:" not in out.getvalue()
    assert not LayoutTemplate.objects.filter(flavor_key="retail").exists()


# ── API ──────────────────────────────────────────────────────────────────


@pytest.fixture
def authed_client(mint_token, mock_jwks):
    client = APIClient()
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "user@cybercom.io",
        "tenant_id": str(uuid.uuid4()),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = mint_token(payload)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_flavor_list_api_returns_catalog(authed_client):
    result = flavors.sync_registry()
    resp = authed_client.get("/api/v1/canonical/flavors/")
    assert resp.status_code == 200
    # default pagination page size is smaller than the full ~55-flavor catalog
    # and results sort alphabetically by key, so assert on the total count
    # rather than scanning page 1 for a specific late-alphabet key.
    assert resp.data["count"] == result["total"]


@pytest.mark.django_db
def test_flavor_list_api_filters_by_status(authed_client):
    flavors.sync_registry()
    resp = authed_client.get("/api/v1/canonical/flavors/?status=ga")
    assert resp.status_code == 200
    assert {row["key"] for row in resp.data["results"]} == {"retail", "clinic"}


@pytest.mark.django_db
def test_flavor_sync_api_admin_action(authed_client):
    resp = authed_client.post("/api/v1/canonical/flavors/sync/")
    assert resp.status_code == 200
    assert resp.data["registry"]["total"] > 0
    assert "retail" in resp.data["packs"]["keys"]
    assert VerticalFlavor.objects.filter(key="retail").exists()


@pytest.mark.django_db
def test_flavor_detail_api_by_key(authed_client):
    flavors.sync_registry()
    resp = authed_client.get("/api/v1/canonical/flavors/retail/")
    assert resp.status_code == 200
    assert resp.data["key"] == "retail"
    assert resp.data["name"] == "RetailFlavour"
