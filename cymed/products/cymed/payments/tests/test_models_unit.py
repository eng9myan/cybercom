from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_unified_bill_defaults_and_bill_number(tenant, patient):
    from products.cymed.payments.models import UnifiedBill

    bill = UnifiedBill.objects.create(tenant_id=tenant, patient_profile=patient)

    assert bill.status == "draft"
    assert bill.subtotal == Decimal("0")
    assert bill.total == Decimal("0")
    assert bill.patient_due == Decimal("0")
    assert bill.insurance_paid == Decimal("0")
    assert bill.bill_number.startswith("BILL-")
    # bill_number is unique + token_hex(6).upper() → 12 hex chars → 17 chars total
    assert len(bill.bill_number) == len("BILL-") + 12


@pytest.mark.django_db
def test_bill_line_item_recompute_totals(tenant, patient, provider_tenant):
    from products.cymed.payments.models import BillLineItem, UnifiedBill

    bill = UnifiedBill.objects.create(tenant_id=tenant, patient_profile=patient)
    BillLineItem.objects.create(
        tenant_id=tenant,
        bill=bill,
        provider_tenant_id=provider_tenant,
        service_code="LAB-CBC",
        service_name="Complete blood count",
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        amount=Decimal("50.00"),
        vat=Decimal("7.50"),
        category="lab",
        insurance_paid=Decimal("20.00"),
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
        insurance_paid=Decimal("0"),
    )

    bill.recompute()
    bill.refresh_from_db()

    assert bill.subtotal == Decimal("150.00")
    assert bill.vat == Decimal("22.50")
    assert bill.total == Decimal("172.50")
    assert bill.insurance_paid == Decimal("20.00")
    assert bill.patient_due == Decimal("152.50")


@pytest.mark.django_db
def test_patient_wallet_defaults(tenant, patient):
    from products.cymed.payments.models import PatientWallet

    wallet = PatientWallet.objects.create(tenant_id=tenant, profile=patient)
    assert wallet.currency == "SAR"
    assert wallet.balance == Decimal("0")
    assert wallet.top_up_locked is False


@pytest.mark.django_db
def test_payment_method_defaults_and_choices(tenant, patient):
    from products.cymed.payments.models import PaymentMethod

    method = PaymentMethod.objects.create(
        tenant_id=tenant,
        profile=patient,
        type="card",
        gateway="stripe",
        gateway_token="tok_xyz",
    )
    assert method.is_default is False
    assert method.brand == ""
    assert method.last4 == ""
    assert method.type == "card"
    assert method.gateway == "stripe"
    # PCI-safe: token is stored, never a raw PAN
    assert method.gateway_token == "tok_xyz"


@pytest.mark.django_db
def test_insurance_policy_defaults(tenant, patient):
    from products.cymed.payments.models import InsurancePolicy

    policy = InsurancePolicy.objects.create(
        tenant_id=tenant,
        profile=patient,
        insurer_code="BUPA",
        policy_number="P-001",
        member_no="M-001",
    )
    assert policy.deductible_met == Decimal("0")
    assert policy.pre_auth_required == []
    assert policy.excluded_services == []
    assert policy.verified_at is None
    assert policy.insurer_code == "BUPA"


@pytest.mark.django_db
def test_payment_transaction_defaults(tenant, patient, sample_bill, sample_method):
    from products.cymed.payments.models import PaymentTransaction

    txn = PaymentTransaction.objects.create(
        tenant_id=tenant,
        bill=sample_bill,
        payer_profile=patient,
        payee_profile=patient,
        payment_method=sample_method,
        amount=Decimal("50.00"),
    )
    assert txn.status == "pending"
    assert txn.currency == "SAR"
    assert txn.txn_number.startswith("TXN-")
    assert len(txn.txn_number) == len("TXN-") + 12
    assert txn.completed_at is None


@pytest.mark.django_db
def test_payment_request_generates_unique_token(tenant, patient, sample_bill):
    from products.cymed.payments.models import PaymentRequest

    expires = timezone.now() + timedelta(hours=24)
    r1 = PaymentRequest.objects.create(
        tenant_id=tenant,
        bill=sample_bill,
        requester_profile=patient,
        amount=Decimal("100.00"),
        expires_at=expires,
    )
    r2 = PaymentRequest.objects.create(
        tenant_id=tenant,
        bill=sample_bill,
        requester_profile=patient,
        amount=Decimal("100.00"),
        expires_at=expires,
    )
    assert r1.token != r2.token
    # secrets.token_urlsafe(48) → ~64 url-safe chars
    assert len(r1.token) >= 60
    assert r1.used_at is None
    assert r1.transaction is None


@pytest.mark.django_db
def test_installment_defaults(tenant, sample_bill):
    from products.cymed.payments.models import Installment

    plan = Installment.objects.create(
        tenant_id=sample_bill.tenant_id,
        bill=sample_bill,
        provider="tabby",
        plan_reference="TAB-XYZ",
        number_of_installments=4,
        monthly_amount=Decimal("25.00"),
    )
    assert plan.status == "active"
    assert plan.number_of_installments == 4
    assert plan.monthly_amount == Decimal("25.00")


@pytest.mark.django_db
def test_revenue_settlement_defaults(tenant, patient, sample_bill, sample_method, provider_tenant):
    from products.cymed.payments.models import PaymentTransaction, RevenueSettlement

    txn = PaymentTransaction.objects.create(
        tenant_id=tenant,
        bill=sample_bill,
        payer_profile=patient,
        payee_profile=patient,
        payment_method=sample_method,
        amount=Decimal("100.00"),
        status="succeeded",
    )
    settlement = RevenueSettlement.objects.create(
        tenant_id=tenant,
        transaction=txn,
        provider_tenant_id=provider_tenant,
        amount=Decimal("95.00"),
    )
    assert settlement.commission == Decimal("0")
    assert settlement.payout_at is None
    assert settlement.amount == Decimal("95.00")
    assert settlement.provider_tenant_id == provider_tenant


@pytest.mark.django_db
def test_eligibility_check_defaults(tenant, patient, provider_tenant):
    from products.cymed.payments.models import EligibilityCheck, InsurancePolicy

    policy = InsurancePolicy.objects.create(
        tenant_id=tenant, profile=patient,
        insurer_code="BUPA", policy_number="P-001", member_no="M-001",
    )
    check = EligibilityCheck.objects.create(
        tenant_id=tenant,
        policy=policy,
        service_code="99213",
        provider_tenant_id=provider_tenant,
        covered=True,
        co_pay_amount=Decimal("15.00"),
    )
    assert check.covered is True
    assert check.requires_preauth is False
    assert check.raw_response == {}
    assert check.checked_at is not None


@pytest.mark.django_db
def test_pre_authorization_defaults(tenant, patient, provider_tenant):
    from products.cymed.payments.models import InsurancePolicy, PreAuthorization

    policy = InsurancePolicy.objects.create(
        tenant_id=tenant, profile=patient,
        insurer_code="BUPA", policy_number="P-001", member_no="M-001",
    )
    pa = PreAuthorization.objects.create(
        tenant_id=tenant,
        policy=policy,
        provider_tenant_id=provider_tenant,
        service_code="MRI-BRAIN",
        clinical_justification="Persistent headache; rule out mass effect.",
    )
    assert pa.status == "pending"
    assert pa.reference_number == ""
    assert pa.approved_amount is None
    assert pa.raw_response == {}
