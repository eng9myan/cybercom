"""The payer on a delegated payment link is the signed-in patient, never a
profile id taken from the request body (2026-10-02 audit)."""
import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cymed.payments.models import PaymentMethod, PaymentRequest, PaymentTransaction


def _patient_client(mint_token, tenant, user_id):
    c = APIClient()
    tok = mint_token({"sub": str(user_id), "email": "p@x.io", "tenant_id": str(tenant),
                      "realm_access": {"roles": ["patient"]}, "roles": ["patient"]})
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}", HTTP_X_TENANT_ID=str(tenant))
    return c


@pytest.fixture
def link(tenant, patient, sample_bill):
    return PaymentRequest.objects.create(
        tenant_id=tenant, bill=sample_bill, requester_profile=patient,
        amount=Decimal("100.00"), expires_at=timezone.now() + timedelta(days=1),
    )


@pytest.fixture
def victim_method(tenant, patient):
    return PaymentMethod.objects.create(
        tenant_id=tenant, profile=patient, type="card", gateway="stripe", gateway_token="tok_victim",
    )


@pytest.mark.django_db
def test_caller_without_a_patient_profile_cannot_pay(mint_token, mock_jwks, tenant, patient, link, victim_method):
    stranger = _patient_client(mint_token, tenant, uuid.uuid4())
    resp = stranger.post(f"/api/v1/payments/payment-requests/{link.token}/", {
        "method_id": str(victim_method.id), "payer_profile_id": str(patient.id),
    }, format="json")
    assert resp.status_code == 401
    assert not PaymentTransaction.objects.exists()


@pytest.mark.django_db
def test_payer_cannot_charge_another_patients_method(
    mint_token, mock_jwks, tenant, patient, link, victim_method, db_patient
):
    from products.cymed.core.patients.models import Patient
    from products.cymed.patient_portal.models import PatientPortalProfile

    other_patient = Patient.objects.create(
        tenant_id=tenant, first_name="Other", last_name="Payer", dob=db_patient.dob,
        mrn=f"MRN-{uuid.uuid4().hex[:8]}",
    )
    payer_user = uuid.uuid4()
    PatientPortalProfile.objects.create(tenant_id=tenant, patient=other_patient, user_id=payer_user)
    resp = _patient_client(mint_token, tenant, payer_user).post(
        f"/api/v1/payments/payment-requests/{link.token}/",
        {"method_id": str(victim_method.id), "payer_profile_id": str(patient.id)}, format="json",
    )
    assert resp.status_code == 404
    assert not PaymentTransaction.objects.exists()
    link.refresh_from_db()
    assert link.used_at is None


@pytest.mark.django_db
def test_patient_can_open_their_own_wallet(mint_token, mock_jwks, tenant, patient):
    resp = _patient_client(mint_token, tenant, patient.user_id).get("/api/v1/payments/wallet/")
    assert resp.status_code == 200
