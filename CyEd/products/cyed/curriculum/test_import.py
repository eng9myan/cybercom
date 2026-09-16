import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.curriculum.importer import import_outcomes
from products.cyed.curriculum.models import CurriculumOutcome


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token(
            {"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
             "realm_access": {"roles": roles}}
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.mark.django_db
def test_importer_upserts_and_is_idempotent(tenant_id):
    rows = [
        {"code": "AC9M7N01", "learning_area": "Mathematics", "year_level": 7, "content_description": "Primes."},
        {"code": "AC9E7LA01", "learning_area": "English", "year_level": "Foundation", "content_description": "Language."},
        {"code": "", "learning_area": "Science", "content_description": "bad row"},
    ]
    res = import_outcomes(tenant_id, rows)
    assert res["created"] == 2
    assert res["skipped"] == 1
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 2
    # "Foundation" year maps to 0.
    assert CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9E7LA01").year_level == 0

    # Re-run updates, does not duplicate.
    rows[0]["content_description"] = "Represent primes with index notation."
    res2 = import_outcomes(tenant_id, rows)
    assert res2["updated"] == 2
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 2
    assert "index notation" in CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N01").content_description


@pytest.mark.django_db
def test_bulk_import_api_is_staff_only(client_for, tenant_id):
    payload = {"outcomes": [
        {"code": "AC9M8N01", "learning_area": "Mathematics", "year_level": 8, "content_description": "Irrational numbers."}
    ]}

    parent = client_for(["parent"], email="p@home.com")
    assert parent.post("/api/v1/curriculum/outcomes/bulk_import/", payload, format="json").status_code == 403

    admin = client_for(["tenant_admin"])
    resp = admin.post("/api/v1/curriculum/outcomes/bulk_import/", payload, format="json")
    assert resp.status_code == 200
    assert resp.data["created"] == 1
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9M8N01").exists()


@pytest.mark.django_db
def test_import_command_loads_starter_set(tenant_id):
    from django.core.management import call_command

    call_command("import_curriculum", tenant=str(tenant_id))
    count = CurriculumOutcome.objects.filter(tenant_id=tenant_id).count()
    # Bundled starter set spans multiple learning areas and year levels.
    assert count >= 25
    areas = set(CurriculumOutcome.objects.filter(tenant_id=tenant_id).values_list("learning_area", flat=True))
    assert {"Mathematics", "English", "Science"}.issubset(areas)
