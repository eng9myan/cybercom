from __future__ import annotations

import uuid
from decimal import Decimal

import pytest


class _FakeChargeResult:
    """Duck-typed stand-in for gateways.base.ChargeResult."""

    def __init__(self, success: bool, status: str = "succeeded",
                 gateway_reference: str = "gw-ref-1",
                 raw: dict | None = None, error_message: str = ""):
        self.success = success
        self.status = status
        self.gateway_reference = gateway_reference
        self.raw = raw or {}
        self.error_message = error_message


class _FakeGateway:
    """Records the last charge call so tests can assert on it."""

    def __init__(self, result: _FakeChargeResult):
        self._result = result
        self.last_call: dict | None = None

    def charge(self, token, amount, currency, metadata):
        self.last_call = {
            "token": token,
            "amount": amount,
            "currency": currency,
            "metadata": metadata,
        }
        return self._result


@pytest.mark.django_db
def test_pay_bill_happy_path_marks_bill_paid(
    monkeypatch, tenant, patient, sample_bill, sample_method
):
    from products.cymed.payments import services

    fake_gw = _FakeGateway(
        _FakeChargeResult(success=True, status="succeeded",
                          gateway_reference="hp_ok_123",
                          raw={"id": "hp_ok_123", "result": {"code": "000.000.000"}})
    )
    monkeypatch.setattr(services, "get_gateway", lambda name: fake_gw)

    charge_amount = sample_bill.patient_due
    assert charge_amount > 0, "fixture should set a nonzero patient_due"

    txn = services.pay_bill(
        bill_id=sample_bill.id,
        method_id=sample_method.id,
        payer_profile_id=patient.id,
    )

    assert txn.status == "succeeded"
    assert txn.gateway_reference == "hp_ok_123"
    assert txn.amount == charge_amount
    assert txn.currency == "SAR"
    assert txn.completed_at is not None
    assert txn.on_behalf_note == ""
    assert txn.delegation_id is None

    # Bill state is advanced to paid because prior + charge >= total.
    sample_bill.refresh_from_db()
    assert sample_bill.status == "paid"
    assert sample_bill.paid_at is not None

    # Gateway received the tokenized method + correct metadata.
    assert fake_gw.last_call is not None
    assert fake_gw.last_call["token"] == sample_method.gateway_token
    assert fake_gw.last_call["amount"] == charge_amount
    assert fake_gw.last_call["currency"] == "SAR"
    assert fake_gw.last_call["metadata"]["bill_number"] == sample_bill.bill_number
    assert fake_gw.last_call["metadata"]["payer_id"] == str(patient.id)


@pytest.mark.django_db
def test_pay_bill_partial_payment_marks_bill_partial(
    monkeypatch, tenant, patient, sample_bill, sample_method
):
    from products.cymed.payments import services

    fake_gw = _FakeGateway(
        _FakeChargeResult(success=True, status="succeeded", gateway_reference="hp_partial")
    )
    monkeypatch.setattr(services, "get_gateway", lambda name: fake_gw)

    half = (sample_bill.patient_due / Decimal("2")).quantize(Decimal("0.01"))
    assert half > 0

    txn = services.pay_bill(
        bill_id=sample_bill.id,
        method_id=sample_method.id,
        payer_profile_id=patient.id,
        amount=half,
    )

    assert txn.amount == half
    assert txn.status == "succeeded"
    sample_bill.refresh_from_db()
    assert sample_bill.status == "partial"
    assert sample_bill.paid_at is None


@pytest.mark.django_db
def test_pay_bill_on_behalf_records_note_and_delegation(
    monkeypatch, tenant, patient, sample_bill, sample_method
):
    from products.cymed.payments import services

    fake_gw = _FakeGateway(_FakeChargeResult(success=True))
    monkeypatch.setattr(services, "get_gateway", lambda name: fake_gw)

    delegation = uuid.uuid4()
    txn = services.pay_bill(
        bill_id=sample_bill.id,
        method_id=sample_method.id,
        payer_profile_id=patient.id,
        on_behalf_note="Paid by adult child on behalf of parent",
        delegation_id=delegation,
    )

    assert txn.on_behalf_note == "Paid by adult child on behalf of parent"
    assert txn.delegation_id == delegation
    # Payer/payee split is preserved even when identical here — verified explicitly.
    assert txn.payer_profile_id == patient.id
    assert txn.payee_profile_id == sample_bill.patient_profile_id


@pytest.mark.django_db
def test_pay_bill_gateway_failure_leaves_bill_unchanged(
    monkeypatch, tenant, patient, sample_bill, sample_method
):
    from products.cymed.payments import services

    fake_gw = _FakeGateway(
        _FakeChargeResult(
            success=False,
            status="failed",
            gateway_reference="hp_fail_1",
            raw={"result": {"code": "800.100.100", "description": "insufficient funds"}},
            error_message="insufficient funds",
        )
    )
    monkeypatch.setattr(services, "get_gateway", lambda name: fake_gw)

    original_status = sample_bill.status
    txn = services.pay_bill(
        bill_id=sample_bill.id,
        method_id=sample_method.id,
        payer_profile_id=patient.id,
    )

    # Failed txn is persisted, but bill is NOT advanced.
    assert txn.status == "failed"
    assert txn.completed_at is None
    assert txn.gateway_reference == "hp_fail_1"
    sample_bill.refresh_from_db()
    assert sample_bill.status == original_status
    assert sample_bill.paid_at is None


@pytest.mark.django_db
def test_pay_bill_rejects_method_from_other_profile(
    monkeypatch, tenant, patient, sample_bill, sample_method
):
    """A payer_profile_id that does not own the payment method must not be able to charge it."""
    from products.cymed.payments import services

    fake_gw = _FakeGateway(_FakeChargeResult(success=True))
    monkeypatch.setattr(services, "get_gateway", lambda name: fake_gw)

    from django.core.exceptions import ObjectDoesNotExist

    with pytest.raises(ObjectDoesNotExist):
        services.pay_bill(
            bill_id=sample_bill.id,
            method_id=sample_method.id,
            payer_profile_id=uuid.uuid4(),  # not the owner
        )
