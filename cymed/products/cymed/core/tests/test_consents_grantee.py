"""
CyID ecosystem, Phase 4 — Consent.granted_to_tenant_id lets a tenant that
DIDN'T create a consent still read it (e.g. a pharmacy tenant reading a
consent a clinic tenant created and shared with it), on top of the
existing owning-tenant access. Real cross-tenant read verified end-to-end,
not just at the model level.
"""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cymed.core.consents.models import Consent, ConsentAudit
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
class TestConsentGrantee:
    def _make_patient(self, tenant_id):
        return Patient.objects.create(
            tenant_id=tenant_id,
            first_name="Jane",
            last_name="Doe",
            dob="1990-01-01",
            gender="female",
            mrn=f"MRN-{uuid.uuid4().hex[:10].upper()}",
        )

    def test_owning_tenant_and_granted_tenant_can_both_read(self, mint_token, mock_jwks):
        clinic_tenant = uuid.uuid4()
        pharmacy_tenant = uuid.uuid4()
        other_tenant = uuid.uuid4()
        patient = self._make_patient(clinic_tenant)

        consent = Consent.objects.create(
            tenant_id=clinic_tenant,
            patient=patient,
            category="data_sharing",
            policy_rule="share active prescriptions with granted pharmacy",
            granted_to_tenant_id=pharmacy_tenant,
        )

        # Owning tenant (clinic) reads it.
        clinic_client = _client_for_tenant(clinic_tenant, mint_token, mock_jwks)
        resp = clinic_client.get(f"/api/v1/consents/{consent.id}/")
        assert resp.status_code == 200, resp.content

        # Granted tenant (pharmacy) reads the SAME consent, real cross-tenant access.
        pharmacy_client = _client_for_tenant(pharmacy_tenant, mint_token, mock_jwks)
        resp = pharmacy_client.get(f"/api/v1/consents/{consent.id}/")
        assert resp.status_code == 200, resp.content
        assert resp.data["granted_to_tenant_id"] == str(pharmacy_tenant)

        # A third, ungranted tenant cannot — RLS-style empty queryset, same
        # 404-not-403 pattern every other tenant-scoped model in this repo uses
        # (never reveals whether the object exists to an unauthorized tenant).
        other_client = _client_for_tenant(other_tenant, mint_token, mock_jwks)
        resp = other_client.get(f"/api/v1/consents/{consent.id}/")
        assert resp.status_code == 404

    def test_grant_at_creation_writes_audit_entry(self, mint_token, mock_jwks):
        clinic_tenant = uuid.uuid4()
        pharmacy_tenant = uuid.uuid4()
        patient = self._make_patient(clinic_tenant)
        clinic_client = _client_for_tenant(clinic_tenant, mint_token, mock_jwks)

        resp = clinic_client.post(
            "/api/v1/consents/",
            {
                "patient": str(patient.id),
                "category": "data_sharing",
                "policy_rule": "share with pharmacy",
                "granted_to_tenant_id": str(pharmacy_tenant),
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        consent = Consent.objects.get(id=resp.data["id"])
        audit = ConsentAudit.objects.filter(consent=consent, action="granted_to_tenant").first()
        assert audit is not None
