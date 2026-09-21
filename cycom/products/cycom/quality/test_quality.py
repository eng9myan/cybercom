import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.quality.models import InspectionPlan, NonConformance, QualityCheckpoint


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "qa@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_pass_does_not_open_ncr(admin_client, tenant_id):
    checkpoint = QualityCheckpoint.objects.create(tenant_id=tenant_id, name="Incoming check")
    resp = admin_client.post(
        f"/api/v1/quality/checkpoints/{checkpoint.id}/record-result/", {"result": "pass"}
    )
    assert resp.status_code == 200
    assert resp.data["result"] == "pass"
    assert NonConformance.objects.filter(checkpoint=checkpoint).count() == 0


@pytest.mark.django_db
def test_fail_auto_opens_ncr(admin_client, tenant_id):
    checkpoint = QualityCheckpoint.objects.create(tenant_id=tenant_id, name="Incoming check")
    resp = admin_client.post(
        f"/api/v1/quality/checkpoints/{checkpoint.id}/record-result/",
        {"result": "fail", "notes": "Wrong dimensions"},
    )
    assert resp.status_code == 200
    ncr = NonConformance.objects.get(checkpoint=checkpoint)
    assert ncr.status == "open"
    assert len(resp.data["non_conformances"]) == 1


@pytest.mark.django_db
def test_cannot_record_twice(admin_client, tenant_id):
    checkpoint = QualityCheckpoint.objects.create(
        tenant_id=tenant_id, name="Incoming check", result="pass"
    )
    resp = admin_client.post(
        f"/api/v1/quality/checkpoints/{checkpoint.id}/record-result/", {"result": "fail"}
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_ncr_close_requires_disposition_and_corrective_action(admin_client, tenant_id):
    checkpoint = QualityCheckpoint.objects.create(tenant_id=tenant_id, name="Incoming check")
    admin_client.post(f"/api/v1/quality/checkpoints/{checkpoint.id}/record-result/", {"result": "fail"})
    ncr = NonConformance.objects.get(checkpoint=checkpoint)

    resp = admin_client.post(f"/api/v1/quality/non-conformances/{ncr.id}/close/")
    assert resp.status_code == 400

    admin_client.patch(
        f"/api/v1/quality/non-conformances/{ncr.id}/", {"disposition": "rework"}, format="json"
    )
    resp = admin_client.post(f"/api/v1/quality/non-conformances/{ncr.id}/close/")
    assert resp.status_code == 400  # still missing corrective_action

    admin_client.patch(
        f"/api/v1/quality/non-conformances/{ncr.id}/",
        {"corrective_action": "Re-machined to spec"},
        format="json",
    )
    resp = admin_client.post(f"/api/v1/quality/non-conformances/{ncr.id}/close/")
    assert resp.status_code == 200
    assert resp.data["status"] == "closed"
    assert resp.data["closed_at"] is not None


@pytest.mark.django_db
def test_checkpoint_from_plan_copies_criteria(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/quality/inspection-plans/",
        {
            "name": "Incoming Inspection",
            "criteria": [
                {"sequence": 10, "description": "Check dimensions"},
                {"sequence": 20, "description": "Check certification"},
            ],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    plan_id = resp.data["id"]

    resp = admin_client.post(
        "/api/v1/quality/checkpoints/",
        {"name": "Rebar batch #4", "inspection_plan": plan_id},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert len(resp.data["criterion_results"]) == 2


@pytest.mark.django_db
def test_ad_hoc_checkpoint_without_plan_has_no_criteria(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/quality/checkpoints/", {"name": "Ad hoc check"}, format="json"
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["criterion_results"] == []


@pytest.mark.django_db
def test_tenant_isolation(admin_client):
    QualityCheckpoint.objects.create(tenant_id=uuid.uuid4(), name="Foreign checkpoint")
    resp = admin_client.get("/api/v1/quality/checkpoints/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign checkpoint" for r in rows)
