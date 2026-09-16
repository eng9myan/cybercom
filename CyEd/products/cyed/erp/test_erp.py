import uuid
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from products.cyed.erp import client


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="u@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.mark.django_db
def test_erp_proxy_forwards_to_cycom(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    with patch.object(client, "fetch", return_value=(200, {"results": [{"id": 1, "first_name": "Jane"}]})) as f:
        resp = admin.get("/api/v1/erp/hr/employees/")
    assert resp.status_code == 200
    assert resp.data["results"][0]["first_name"] == "Jane"
    # Path forwarded to CyCom's HR resource.
    assert f.call_args.args[0] == "hr/employees/"


@pytest.mark.django_db
def test_erp_rejects_non_whitelisted(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    resp = admin.get("/api/v1/erp/sis/students/")  # not an ERP resource
    assert resp.status_code == 400


@pytest.mark.django_db
def test_erp_unconfigured_returns_503(client_for, tenant_id, monkeypatch):
    monkeypatch.delenv("CYED_CYCOM_URL", raising=False)
    admin = client_for(["tenant_admin"])
    resp = admin.get("/api/v1/erp/hr/employees/")
    assert resp.status_code == 503


@pytest.mark.django_db
def test_erp_staff_only(client_for, tenant_id):
    parent = client_for(["parent"], email="p@home.com")
    assert parent.get("/api/v1/erp/hr/employees/").status_code == 403
