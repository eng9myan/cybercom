from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest


@pytest.fixture
def tenant():
    """Return a stable tenant UUID for the test session context."""
    return uuid.uuid4()


@pytest.fixture
def provider_tenant():
    """A UUID for a provider tenant used in bill line items / pre-auth."""
    return uuid.uuid4()


@pytest.fixture
def db_patient(db, tenant):
    """A minimal Patient row (core.patients.Patient) usable by patient_portal FKs."""
    from products.cymed.core.patients.models import Patient

    return Patient.objects.create(
        tenant_id=tenant,
        first_name="Test",
        last_name="Payer",
        dob=date(1990, 1, 1),
        mrn=f"MRN-{uuid.uuid4().hex[:10].upper()}",
    )


@pytest.fixture
def patient(db, tenant, db_patient):
    """A PatientPortalProfile — the FK target used everywhere in payments."""
    from products.cymed.patient_portal.models import PatientPortalProfile

    return PatientPortalProfile.objects.create(
        tenant_id=tenant,
        patient=db_patient,
        user_id=uuid.uuid4(),
        preferred_language="en",
    )


@pytest.fixture
def sample_bill(db, tenant, patient, provider_tenant):
    """An issued bill with one line item; totals recomputed from items."""
    from products.cymed.payments.models import BillLineItem, UnifiedBill

    bill = UnifiedBill.objects.create(
        tenant_id=tenant,
        patient_profile=patient,
        subtotal=Decimal("0"),
        total=Decimal("0"),
        patient_due=Decimal("0"),
        status="patient_due",
    )
    BillLineItem.objects.create(
        tenant_id=tenant,
        bill=bill,
        provider_tenant_id=provider_tenant,
        service_code="99213",
        service_name="Office visit",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        amount=Decimal("100.00"),
        vat=Decimal("15.00"),
    )
    bill.recompute()
    bill.refresh_from_db()
    return bill


@pytest.fixture
def sample_method(db, tenant, patient):
    """A saved HyperPay card token for the patient."""
    from products.cymed.payments.models import PaymentMethod

    return PaymentMethod.objects.create(
        tenant_id=tenant,
        profile=patient,
        type="card",
        brand="Visa",
        last4="4242",
        gateway="hyperpay",
        gateway_token="tok_test_abc123",
        holder_name="Test Payer",
        is_default=True,
        expires_at=date.today() + timedelta(days=365),
    )
