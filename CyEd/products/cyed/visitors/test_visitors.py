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
def test_sign_in_and_out(admin, tenant_id):
    v = admin.post("/api/v1/visitors/", {"full_name": "Contractor Dave", "purpose": "AC repair",
                                         "host_name": "Facilities"}, format="json")
    assert v.status_code == 201, v.data
    assert v.data["on_site"] is True

    on_site = admin.get("/api/v1/visitors/?on_site=1").data
    on_site = on_site["results"] if isinstance(on_site, dict) else on_site
    assert len(on_site) == 1

    out = admin.post(f"/api/v1/visitors/{v.data['id']}/sign_out/")
    assert out.status_code == 200
    assert out.data["on_site"] is False
