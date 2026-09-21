import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.hr.models import Employee
from products.cycom.referrals.models import Referral


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


@pytest.fixture
def referrer(db, tenant_id):
    return Employee.objects.create(
        tenant_id=tenant_id,
        employee_number="E-1",
        first_name="Jane",
        last_name="Doe",
        hire_date="2024-01-01",
    )


@pytest.mark.django_db
def test_create_referral(platform_admin_client, tenant_id, referrer):
    resp = platform_admin_client.post(
        "/api/v1/referrals/referrals/",
        {
            "referrer": str(referrer.id),
            "candidate_name": "John Smith",
            "candidate_email": "john@example.com",
            "job_title": "Warehouse Lead",
            "bonus_amount": "200.00",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "submitted"
    assert resp.data["bonus_paid"] is False


@pytest.mark.django_db
def test_bonus_paid_cannot_be_set_via_patch(platform_admin_client, tenant_id, referrer):
    referral = Referral.objects.create(
        tenant_id=tenant_id, referrer=referrer, candidate_name="John Smith", job_title="Lead"
    )
    resp = platform_admin_client.patch(
        f"/api/v1/referrals/referrals/{referral.id}/", {"bonus_paid": True}, format="json"
    )
    assert resp.status_code == 200
    referral.refresh_from_db()
    assert referral.bonus_paid is False


@pytest.mark.django_db
def test_pay_bonus_requires_hired_status(platform_admin_client, tenant_id, referrer):
    referral = Referral.objects.create(
        tenant_id=tenant_id, referrer=referrer, candidate_name="John Smith", job_title="Lead"
    )
    resp = platform_admin_client.post(f"/api/v1/referrals/referrals/{referral.id}/pay-bonus/")
    assert resp.status_code == 400
    referral.refresh_from_db()
    assert referral.bonus_paid is False


@pytest.mark.django_db
def test_pay_bonus_succeeds_when_hired(platform_admin_client, tenant_id, referrer):
    referral = Referral.objects.create(
        tenant_id=tenant_id,
        referrer=referrer,
        candidate_name="John Smith",
        job_title="Lead",
        status="hired",
    )
    resp = platform_admin_client.post(f"/api/v1/referrals/referrals/{referral.id}/pay-bonus/")
    assert resp.status_code == 200
    referral.refresh_from_db()
    assert referral.bonus_paid is True


@pytest.mark.django_db
def test_pay_bonus_twice_rejected(platform_admin_client, tenant_id, referrer):
    referral = Referral.objects.create(
        tenant_id=tenant_id,
        referrer=referrer,
        candidate_name="John Smith",
        job_title="Lead",
        status="hired",
        bonus_paid=True,
    )
    resp = platform_admin_client.post(f"/api/v1/referrals/referrals/{referral.id}/pay-bonus/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_tenant_isolation(platform_admin_client, tenant_id):
    other_tenant = uuid.uuid4()
    other_referrer = Employee.objects.create(
        tenant_id=other_tenant,
        employee_number="E-2",
        first_name="Other",
        last_name="Tenant",
        hire_date="2024-01-01",
    )
    Referral.objects.create(
        tenant_id=other_tenant, referrer=other_referrer, candidate_name="X", job_title="Y"
    )
    resp = platform_admin_client.get("/api/v1/referrals/referrals/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 0
