"""
CyID ecosystem, Phase 5 — Order.fulfilling_tenant_id lets a DIFFERENT
tenant (the one that fulfills the order, e.g. an external pharmacy) see
and act on it, on top of the source tenant that created it. Depends on
Phase 4 (consent) conceptually — same cross-tenant-visibility pattern,
verified independently here at the order level.
"""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cymed.core.orders.models import Order
from products.cymed.core.patients.models import Patient


def _client_for_tenant(tenant_id, mint_token, mock_jwks):
    client = APIClient()
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "user@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": []},
        }
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return client


@pytest.mark.django_db
class TestOrderCrossTenantFulfillment:
    def _make_patient(self, tenant_id):
        return Patient.objects.create(
            tenant_id=tenant_id,
            first_name="Ali",
            last_name="Hassan",
            dob="1985-03-20",
            gender="male",
            mrn=f"MRN-{uuid.uuid4().hex[:10].upper()}",
        )

    def test_source_and_fulfilling_tenant_both_see_order(self, mint_token, mock_jwks):
        clinic_tenant = uuid.uuid4()
        pharmacy_tenant = uuid.uuid4()
        other_tenant = uuid.uuid4()
        patient = self._make_patient(clinic_tenant)

        clinic_client = _client_for_tenant(clinic_tenant, mint_token, mock_jwks)
        resp = clinic_client.post(
            "/api/v1/orders/",
            {
                "patient": str(patient.id),
                "order_type": "medication",
                "ordered_by": "Dr. Noor",
                "fulfilling_tenant_id": str(pharmacy_tenant),
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        order_id = resp.data["id"]

        order = Order.objects.get(id=order_id)
        assert str(order.tenant_id) == str(clinic_tenant)  # source, server-forced
        assert str(order.fulfilling_tenant_id) == str(pharmacy_tenant)

        # Source tenant (clinic) still sees its own order.
        resp = clinic_client.get(f"/api/v1/orders/{order_id}/")
        assert resp.status_code == 200

        # Fulfilling tenant (pharmacy) sees it too — real cross-tenant queue.
        pharmacy_client = _client_for_tenant(pharmacy_tenant, mint_token, mock_jwks)
        resp = pharmacy_client.get(f"/api/v1/orders/{order_id}/")
        assert resp.status_code == 200, resp.content

        # An unrelated tenant cannot.
        other_client = _client_for_tenant(other_tenant, mint_token, mock_jwks)
        resp = other_client.get(f"/api/v1/orders/{order_id}/")
        assert resp.status_code == 404

    def test_order_type_filter_actually_filters(self, mint_token, mock_jwks):
        """Phase 9 — DEFAULT_FILTER_BACKENDS was never configured in cymed
        (same bug already found+fixed in Cycom), so ?order_type= was
        silently ignored. Fixed here since the mobile e-Rx screen depends
        on it."""
        clinic_tenant = uuid.uuid4()
        patient = self._make_patient(clinic_tenant)
        clinic_client = _client_for_tenant(clinic_tenant, mint_token, mock_jwks)

        clinic_client.post(
            "/api/v1/orders/",
            {"patient": str(patient.id), "order_type": "medication", "ordered_by": "Dr. Noor"},
            format="json",
        )
        clinic_client.post(
            "/api/v1/orders/",
            {"patient": str(patient.id), "order_type": "laboratory", "ordered_by": "Dr. Noor"},
            format="json",
        )

        resp = clinic_client.get("/api/v1/orders/?order_type=medication")
        assert resp.status_code == 200, resp.content
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["order_type"] == "medication"

    def test_tenant_id_cannot_be_spoofed_by_client(self, mint_token, mock_jwks):
        clinic_tenant = uuid.uuid4()
        spoofed_tenant = uuid.uuid4()
        patient = self._make_patient(clinic_tenant)
        clinic_client = _client_for_tenant(clinic_tenant, mint_token, mock_jwks)

        resp = clinic_client.post(
            "/api/v1/orders/",
            {
                "patient": str(patient.id),
                "order_type": "laboratory",
                "ordered_by": "Dr. Noor",
                "tenant_id": str(spoofed_tenant),  # ignored — server forces the real one
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        order = Order.objects.get(id=resp.data["id"])
        assert str(order.tenant_id) == str(clinic_tenant)
