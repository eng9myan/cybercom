"""
Payment tests.

Weighted toward the ways a payment system loses money or leaks data, not
toward the happy path: double charging, over-refunding, paying someone else's
invoice, forged webhooks, replayed webhooks, and a provider that is configured
but not implemented.
"""

import hashlib
import hmac
import json
import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.fees.models import Invoice, Payment
from products.cyed.payments.models import PaymentIntent, WebhookEvent
from products.cyed.sis.models import Guardian, Student

WEBHOOK_SECRET = "test-webhook-secret"


# ── fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def mock_provider(monkeypatch):
    """Every test runs against the deterministic mock gateway by default."""
    monkeypatch.setenv("CYED_PAYMENT_PROVIDER", "mock")
    monkeypatch.setenv("CYED_PAYMENT_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.delenv("CYED_PAYMENT_MOCK_FAIL", raising=False)


def _client(mint_token, mock_jwks, tenant_id, roles, email):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": email,
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": roles},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def finance_client(mint_token, mock_jwks, tenant_id):
    return _client(mint_token, mock_jwks, tenant_id, ["finance"], "bursar@cyed.edu.au")


@pytest.fixture
def parent_client(mint_token, mock_jwks, tenant_id):
    return _client(mint_token, mock_jwks, tenant_id, ["parent"], "parent@example.com")


@pytest.fixture
def other_parent_client(mint_token, mock_jwks, tenant_id):
    return _client(mint_token, mock_jwks, tenant_id, ["parent"], "stranger@example.com")


@pytest.fixture
def family(tenant_id):
    """One student, one guardian whose email matches `parent_client`, one invoice."""
    student = Student.objects.create(
        tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8
    )
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Lan", last_name="Nguyen", email="parent@example.com"
    )
    guardian.students.add(student)
    invoice = Invoice.objects.create(
        tenant_id=tenant_id, student=student, description="Term 1 Tuition",
        amount=Decimal("1000.00"), status="issued",
    )
    return student, guardian, invoice


def _sign(body: bytes) -> str:
    return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


def _post_webhook(client, payload: dict, provider="mock", signature=None):
    body = json.dumps(payload).encode()
    return client.post(
        f"/api/v1/public/payments/webhook/{provider}/",
        data=body,
        content_type="application/json",
        HTTP_X_CYED_SIGNATURE=signature if signature is not None else _sign(body),
    )


# ── the core promise: money moves once, and lands on the ledger ──────────────
@pytest.mark.django_db
def test_capture_credits_the_invoice_ledger(finance_client, tenant_id, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "400.00", "idempotency_key": "k-1", "invoice": str(invoice.id), "method": "card"},
        format="json",
    )
    assert created.status_code == 201, created.data
    assert created.data["status"] == "pending"

    captured = finance_client.post(f"/api/v1/payments/intents/{created.data['id']}/capture/", {}, format="json")
    assert captured.status_code == 200, captured.data
    assert captured.data["status"] == "succeeded"
    assert captured.data["reconciled_at"] is not None

    invoice.refresh_from_db()
    assert invoice.status == "partial"
    assert Payment.objects.filter(invoice=invoice, amount=Decimal("400.00")).count() == 1


@pytest.mark.django_db
def test_replaying_the_idempotency_key_does_not_charge_twice(finance_client, tenant_id, family):
    """The single most important property: a parent who retries pays once."""
    _, _, invoice = family
    body = {"amount": "250.00", "idempotency_key": "same-key", "invoice": str(invoice.id)}

    first = finance_client.post("/api/v1/payments/intents/", body, format="json")
    second = finance_client.post("/api/v1/payments/intents/", body, format="json")

    assert first.status_code == 201
    # 200, not 201 — nothing new was created and the client must be able to tell.
    assert second.status_code == 200
    assert first.data["id"] == second.data["id"]
    assert PaymentIntent.objects.filter(tenant_id=tenant_id).count() == 1


@pytest.mark.django_db
def test_capturing_twice_is_a_no_op_not_a_double_credit(finance_client, tenant_id, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "k-2", "invoice": str(invoice.id)},
        format="json",
    )
    url = f"/api/v1/payments/intents/{created.data['id']}/capture/"
    assert finance_client.post(url, {}, format="json").status_code == 200
    assert finance_client.post(url, {}, format="json").status_code == 200

    invoice.refresh_from_db()
    assert invoice.status == "paid"
    assert Payment.objects.filter(invoice=invoice).count() == 1


@pytest.mark.django_db
def test_cannot_capture_more_than_authorised(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "k-3", "invoice": str(invoice.id)},
        format="json",
    )
    over = finance_client.post(
        f"/api/v1/payments/intents/{created.data['id']}/capture/",
        {"amount": "500.00"}, format="json",
    )
    assert over.status_code == 400
    assert "only authorised for" in over.data["detail"]


# ── refunds ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_partial_refund_reverses_on_the_ledger_and_reopens_the_invoice(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "k-4", "invoice": str(invoice.id)},
        format="json",
    )
    intent_id = created.data["id"]
    finance_client.post(f"/api/v1/payments/intents/{intent_id}/capture/", {}, format="json")
    invoice.refresh_from_db()
    assert invoice.status == "paid"

    refunded = finance_client.post(
        f"/api/v1/payments/intents/{intent_id}/refund/",
        {"amount": "300.00", "reason": "overpaid"}, format="json",
    )
    assert refunded.status_code == 201, refunded.data
    assert refunded.data["status"] == "succeeded"

    invoice.refresh_from_db()
    # A negative payment row makes the ledger's own recalc drop it back to
    # partial — no parallel refund bookkeeping to drift out of sync.
    assert invoice.status == "partial"
    assert Payment.objects.filter(invoice=invoice, amount=Decimal("-300.00")).count() == 1

    intent = PaymentIntent.objects.get(id=intent_id)
    assert intent.refunded_amount == Decimal("300.00")
    assert intent.status == "succeeded"  # partial refund does not close the intent


@pytest.mark.django_db
def test_cannot_refund_more_than_captured(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "k-5", "invoice": str(invoice.id)},
        format="json",
    )
    intent_id = created.data["id"]
    finance_client.post(f"/api/v1/payments/intents/{intent_id}/capture/", {}, format="json")

    first = finance_client.post(
        f"/api/v1/payments/intents/{intent_id}/refund/", {"amount": "60.00"}, format="json"
    )
    assert first.status_code == 201
    over = finance_client.post(
        f"/api/v1/payments/intents/{intent_id}/refund/", {"amount": "60.00"}, format="json"
    )
    assert over.status_code == 400
    assert "exceeds the refundable balance" in over.data["detail"]


@pytest.mark.django_db
def test_full_refund_closes_the_intent(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "k-6", "invoice": str(invoice.id)},
        format="json",
    )
    intent_id = created.data["id"]
    finance_client.post(f"/api/v1/payments/intents/{intent_id}/capture/", {}, format="json")
    finance_client.post(f"/api/v1/payments/intents/{intent_id}/refund/", {}, format="json")

    assert PaymentIntent.objects.get(id=intent_id).status == "refunded"


@pytest.mark.django_db
def test_uncaptured_intent_cannot_be_refunded(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "k-7", "invoice": str(invoice.id)},
        format="json",
    )
    resp = finance_client.post(
        f"/api/v1/payments/intents/{created.data['id']}/refund/", {}, format="json"
    )
    assert resp.status_code == 400
    assert "Only a captured payment can be refunded" in resp.data["detail"]


# ── access control ───────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_parent_may_pay_their_own_childs_invoice(parent_client, family):
    _, _, invoice = family
    resp = parent_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "p-1", "invoice": str(invoice.id)},
        format="json",
    )
    assert resp.status_code == 201, resp.data


@pytest.mark.django_db
def test_parent_cannot_pay_another_familys_invoice(other_parent_client, family):
    """
    404, not 403: a distinguishable 'forbidden' would confirm the invoice
    exists and turn this endpoint into an invoice enumerator.
    """
    _, _, invoice = family
    resp = other_parent_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "p-2", "invoice": str(invoice.id)},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_parent_cannot_capture_or_refund(parent_client, finance_client, family):
    """A parent asserting 'the money arrived' would be marking their own homework."""
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "p-3", "invoice": str(invoice.id)},
        format="json",
    )
    intent_id = created.data["id"]
    assert parent_client.post(f"/api/v1/payments/intents/{intent_id}/capture/", {}, format="json").status_code == 403
    assert parent_client.post(f"/api/v1/payments/intents/{intent_id}/refund/", {}, format="json").status_code == 403


@pytest.mark.django_db
def test_parent_list_is_scoped_to_their_children(parent_client, other_parent_client, finance_client, family):
    _, _, invoice = family
    finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "p-4", "invoice": str(invoice.id)},
        format="json",
    )
    mine = parent_client.get("/api/v1/payments/intents/")
    theirs = other_parent_client.get("/api/v1/payments/intents/")
    assert mine.status_code == 200 and len(mine.data["results"]) == 1
    assert theirs.status_code == 200 and len(theirs.data["results"]) == 0


@pytest.mark.django_db
def test_intents_are_not_editable_over_the_api(finance_client, family):
    """No PUT/PATCH: status and captured_amount belong to the gateway."""
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "p-5", "invoice": str(invoice.id)},
        format="json",
    )
    resp = finance_client.patch(
        f"/api/v1/payments/intents/{created.data['id']}/",
        {"status": "succeeded", "captured_amount": "100.00"}, format="json",
    )
    assert resp.status_code == 405


# ── webhooks ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_signed_webhook_settles_and_reconciles(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "w-1", "invoice": str(invoice.id)},
        format="json",
    )
    resp = _post_webhook(APIClient(), {
        "id": "evt_1", "type": "payment_intent.succeeded",
        "data": {"intent_id": created.data["id"], "amount": "1000.00"},
    })
    assert resp.status_code == 200, resp.data
    assert resp.data["result"] == "applied"

    invoice.refresh_from_db()
    assert invoice.status == "paid"
    assert Payment.objects.filter(invoice=invoice).count() == 1


@pytest.mark.django_db
def test_forged_signature_is_rejected_and_recorded(finance_client, family):
    """A forged callback is evidence. It must be stored, not dropped."""
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "w-2", "invoice": str(invoice.id)},
        format="json",
    )
    resp = _post_webhook(APIClient(), {
        "id": "evt_forged", "type": "payment_intent.succeeded",
        "data": {"intent_id": created.data["id"], "amount": "1000.00"},
    }, signature="deadbeef")

    assert resp.status_code == 400
    assert resp.data["result"] == "rejected_signature"
    assert WebhookEvent.objects.filter(result="rejected_signature").count() == 1
    invoice.refresh_from_db()
    assert invoice.status == "issued"          # untouched
    assert Payment.objects.filter(invoice=invoice).count() == 0


@pytest.mark.django_db
def test_replayed_webhook_does_not_credit_twice(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "w-3", "invoice": str(invoice.id)},
        format="json",
    )
    event = {
        "id": "evt_replay", "type": "payment_intent.succeeded",
        "data": {"intent_id": created.data["id"], "amount": "1000.00"},
    }
    first = _post_webhook(APIClient(), event)
    second = _post_webhook(APIClient(), event)

    assert first.data["result"] == "applied"
    # A provider retrying a delivery is normal traffic, not an error.
    assert second.status_code == 200
    assert second.data["result"] == "duplicate"
    assert Payment.objects.filter(invoice=invoice).count() == 1


@pytest.mark.django_db
def test_webhook_claiming_more_than_the_intent_is_refused(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "w-4", "invoice": str(invoice.id)},
        format="json",
    )
    resp = _post_webhook(APIClient(), {
        "id": "evt_over", "type": "payment_intent.succeeded",
        "data": {"intent_id": created.data["id"], "amount": "999999.00"},
    })
    assert resp.status_code == 400
    assert resp.data["result"] == "error"
    assert Payment.objects.filter(invoice=invoice).count() == 0


@pytest.mark.django_db
def test_webhook_without_a_configured_secret_is_refused(finance_client, family, monkeypatch):
    """
    No shared secret means we cannot tell the provider from an attacker.
    503, and nothing is applied.
    """
    monkeypatch.delenv("CYED_PAYMENT_WEBHOOK_SECRET", raising=False)
    resp = APIClient().post(
        "/api/v1/public/payments/webhook/mock/",
        data=json.dumps({"id": "evt_x", "type": "payment_intent.succeeded", "data": {}}).encode(),
        content_type="application/json",
        HTTP_X_CYED_SIGNATURE="anything",
    )
    assert resp.status_code == 503
    assert resp.data["result"] == "rejected_unconfigured"


@pytest.mark.django_db
def test_unmatched_webhook_is_recorded_against_the_sentinel_tenant():
    resp = _post_webhook(APIClient(), {
        "id": "evt_nomatch", "type": "payment_intent.succeeded",
        "data": {"provider_reference": "mock_pi_does_not_exist"},
    })
    assert resp.status_code == 200
    assert resp.data["result"] == "unmatched"


# ── provider configuration ───────────────────────────────────────────────────
@pytest.mark.django_db
def test_unimplemented_provider_fails_loudly_rather_than_faking_success(
    finance_client, family, monkeypatch
):
    """
    A deployment that sets CYED_PAYMENT_PROVIDER=stripe before the adapter
    exists must break on the first charge, not quietly record intents as
    succeeded while collecting nothing.
    """
    _, _, invoice = family
    monkeypatch.setenv("CYED_PAYMENT_PROVIDER", "stripe")
    resp = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "u-1", "invoice": str(invoice.id)},
        format="json",
    )
    assert resp.status_code == 503
    assert "no adapter or credentials configured" in resp.data["detail"]
    # No half-open intent may survive: the idempotency key is unique per tenant,
    # so an orphaned `created` row would make every later retry return that
    # stale unauthorised intent even after the provider is configured properly.
    assert PaymentIntent.objects.count() == 0

    # Once a working provider is configured, the same key must go through.
    monkeypatch.setenv("CYED_PAYMENT_PROVIDER", "mock")
    retry = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "u-1", "invoice": str(invoice.id)},
        format="json",
    )
    assert retry.status_code == 201, retry.data
    assert retry.data["status"] == "pending"


@pytest.mark.django_db
def test_declined_payment_leaves_the_invoice_alone(finance_client, family, monkeypatch):
    _, _, invoice = family
    monkeypatch.setenv("CYED_PAYMENT_MOCK_FAIL", "1")
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "100.00", "idempotency_key": "d-1", "invoice": str(invoice.id)},
        format="json",
    )
    assert created.status_code == 201
    assert created.data["status"] == "failed"
    assert created.data["failure_reason"] == "mock_declined"

    invoice.refresh_from_db()
    assert invoice.status == "issued"
    assert Payment.objects.filter(invoice=invoice).count() == 0


@pytest.mark.django_db
def test_manual_provider_models_an_offline_bpay_payment(finance_client, family, monkeypatch):
    """
    How most Australian schools actually take fees today: issue a reference,
    then confirm the money landed. Authorisation must NOT credit the ledger.
    """
    _, _, invoice = family
    monkeypatch.setenv("CYED_PAYMENT_PROVIDER", "manual")
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "m-1", "invoice": str(invoice.id), "method": "bpay"},
        format="json",
    )
    assert created.status_code == 201
    assert created.data["status"] == "pending"
    assert created.data["provider_reference"].startswith("MANUAL-")
    invoice.refresh_from_db()
    assert invoice.status == "issued"  # a reference is not money

    finance_client.post(f"/api/v1/payments/intents/{created.data['id']}/capture/", {}, format="json")
    invoice.refresh_from_db()
    assert invoice.status == "paid"


# ── reconciliation reporting ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_reconciliation_report_is_empty_when_everything_posted(finance_client, family):
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "r-1", "invoice": str(invoice.id)},
        format="json",
    )
    finance_client.post(f"/api/v1/payments/intents/{created.data['id']}/capture/", {}, format="json")

    report = finance_client.get("/api/v1/payments/intents/reconciliation-report/")
    assert report.status_code == 200
    assert report.data["count"] == 0


@pytest.mark.django_db
def test_reconciliation_report_flags_captured_money_never_posted(finance_client, tenant_id, family):
    """Money taken and not credited is the discrepancy that matters most."""
    _, _, invoice = family
    created = finance_client.post(
        "/api/v1/payments/intents/",
        {"amount": "1000.00", "idempotency_key": "r-2", "invoice": str(invoice.id)},
        format="json",
    )
    finance_client.post(f"/api/v1/payments/intents/{created.data['id']}/capture/", {}, format="json")

    # Simulate the ledger row vanishing (a bad manual edit, a failed migration).
    Payment.objects.filter(invoice=invoice).delete()

    report = finance_client.get("/api/v1/payments/intents/reconciliation-report/")
    assert report.data["count"] == 1
    assert report.data["rows"][0]["discrepancy"] == "captured_not_posted"


@pytest.mark.django_db
def test_webhook_event_log_is_read_only(finance_client):
    resp = finance_client.post(
        "/api/v1/payments/webhook-events/",
        {"provider": "mock", "result": "applied"}, format="json",
    )
    assert resp.status_code == 405
