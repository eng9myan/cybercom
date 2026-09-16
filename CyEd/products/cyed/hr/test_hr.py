import uuid

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def admin(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "email": "a@cyed.edu.au", "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["tenant_admin"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


@pytest.mark.django_db
def test_staff_contract_leave(admin, tenant_id):
    s = admin.post("/api/v1/hr/staff/", {"first_name": "Jane", "last_name": "Doe", "role": "teacher"}, format="json")
    assert s.status_code == 201, s.data
    sid = s.data["id"]
    c = admin.post("/api/v1/hr/contracts/",
                   {"staff": sid, "contract_type": "full_time", "annual_salary": "85000"}, format="json")
    assert c.status_code == 201, c.data
    lv = admin.post("/api/v1/hr/leave/",
                    {"staff": sid, "leave_type": "annual", "days": "5", "status": "requested"}, format="json")
    assert lv.status_code == 201


@pytest.mark.django_db
def test_hr_staff_only(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "email": "p@home.com", "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["parent"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert c.get("/api/v1/hr/staff/").status_code == 403
