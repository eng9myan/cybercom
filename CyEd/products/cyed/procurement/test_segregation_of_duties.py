"""Segregation of duties: nobody approves their own purchase request."""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.procurement.models import Supplier


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="u@cyed.edu.au"):
        t = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                        "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {t}")
        return c
    return _make


def _raise_request(client, tenant_id, supplier):
    pr = client.post("/api/v1/procurement/requests/",
                     {"department": "IT", "suggested_supplier": str(supplier.id)}, format="json")
    client.post("/api/v1/procurement/request-lines/",
                {"request": pr.data["id"], "description": "Monitor",
                 "quantity": "1", "estimated_unit_price": "100"}, format="json")
    client.post(f"/api/v1/procurement/requests/{pr.data['id']}/submit/")
    return pr.data["id"]


@pytest.mark.django_db
def test_finance_cannot_self_approve_own_request(client_for, tenant_id):
    sup = Supplier.objects.create(tenant_id=tenant_id, name="Vendor")
    fin = client_for(["finance"], email="fin@cyed.edu.au")
    pr_id = _raise_request(fin, tenant_id, sup)

    denied = fin.post(f"/api/v1/procurement/requests/{pr_id}/approve/", {"level": 1}, format="json")
    assert denied.status_code == 403
    assert "yourself" in denied.data["detail"].lower()

    # A different finance officer may approve it.
    other = client_for(["finance"], email="fin2@cyed.edu.au")
    ok = other.post(f"/api/v1/procurement/requests/{pr_id}/approve/", {"level": 1}, format="json")
    assert ok.status_code == 200
    assert ok.data["status"] == "approved"


@pytest.mark.django_db
def test_requester_may_still_reject_own_request(client_for, tenant_id):
    """Withdrawing your own request is legitimate — only self-*approval* is barred."""
    sup = Supplier.objects.create(tenant_id=tenant_id, name="Vendor")
    fin = client_for(["finance"], email="fin@cyed.edu.au")
    pr_id = _raise_request(fin, tenant_id, sup)

    rejected = fin.post(f"/api/v1/procurement/requests/{pr_id}/reject/",
                        {"level": 1, "comment": "No longer needed"}, format="json")
    assert rejected.status_code == 200
    assert rejected.data["status"] == "rejected"
