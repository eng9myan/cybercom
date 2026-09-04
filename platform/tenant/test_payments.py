"""Payment seam + activation-path tests (provider-agnostic subscription billing)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings

from platform.tenant.models import (
    InvoiceStatus,
    SubscriptionPlan,
    Tenant,
    TenantStatus,
    TenantSubscription,
    TenantSubscriptionInvoice,
    TenantType,
)
from platform.tenant.payments import (
    ManualBankTransferProvider,
    WebhookVerificationError,
    get_payment_provider,
)
from platform.tenant.services import activate_paid_subscription


def _make_invoice(provider="manual"):
    suffix = uuid.uuid4().hex[:8]
    tenant = Tenant.objects.create(
        name=f"Acme {suffix}", slug=f"acme-{suffix}",
        tenant_type=TenantType.SAAS, status=TenantStatus.PENDING,
    )
    sub = TenantSubscription.objects.create(
        tenant=tenant, plan=SubscriptionPlan.PROFESSIONAL, is_active=False,
    )
    inv = TenantSubscriptionInvoice.objects.create(
        subscription=sub, invoice_number=f"INV-{suffix}", amount=Decimal("149.00"),
        currency="USD", due_date=date.today() + timedelta(days=7),
        status=InvoiceStatus.PENDING, provider=provider,
    )
    return tenant, sub, inv


class ActivationPathTests(TestCase):
    def test_payment_activates_tenant_and_marks_invoice_paid(self):
        tenant, sub, inv = _make_invoice()
        self.assertEqual(tenant.status, TenantStatus.PENDING)

        activate_paid_subscription(inv, approved_by="test")

        inv.refresh_from_db(); tenant.refresh_from_db(); sub.refresh_from_db()
        self.assertEqual(inv.status, InvoiceStatus.PAID)
        self.assertIsNotNone(inv.paid_at)
        self.assertEqual(tenant.status, TenantStatus.ACTIVE)
        self.assertTrue(sub.is_active)

    def test_activation_is_idempotent(self):
        _, _, inv = _make_invoice()
        activate_paid_subscription(inv, approved_by="first")
        # A webhook retry must not error or double-activate.
        tenant = activate_paid_subscription(inv, approved_by="second")
        self.assertEqual(tenant.status, TenantStatus.ACTIVE)


class ManualProviderTests(TestCase):
    def test_manual_checkout_returns_bank_instructions(self):
        _, _, inv = _make_invoice()
        checkout = ManualBankTransferProvider().create_checkout(inv).as_dict()
        self.assertEqual(checkout["mode"], "manual")
        self.assertEqual(checkout["instructions"]["reference"], inv.invoice_number)
        self.assertEqual(checkout["instructions"]["amount"], "149.00")


@override_settings(DEBUG=True, PAYMENT_PROVIDER="fake")
class FakeProviderTests(TestCase):
    def test_signed_webhook_confirms_payment(self):
        _, _, inv = _make_invoice(provider="fake")
        prov = get_payment_provider("fake")
        body = ('{"invoice_number": "%s", "status": "paid", "ref": "r1"}' % inv.invoice_number).encode()
        event = prov.parse_webhook(body=body, headers={"X-Fake-Signature": prov.sign(inv.invoice_number)})
        self.assertTrue(event.paid)
        self.assertEqual(event.invoice_number, inv.invoice_number)

    def test_bad_signature_rejected(self):
        _, _, inv = _make_invoice(provider="fake")
        prov = get_payment_provider("fake")
        body = ('{"invoice_number": "%s", "status": "paid"}' % inv.invoice_number).encode()
        with self.assertRaises(WebhookVerificationError):
            prov.parse_webhook(body=body, headers={"X-Fake-Signature": "deadbeef"})


class StripeWebhookVerificationTests(SimpleTestCase):
    """Finding-1 regression: the Stripe webhook must verify the HMAC signature
    (fail-closed), so a forged 'paid' event cannot activate a tenant for free."""

    def _prov(self):
        from platform.tenant.payments import StripeProvider
        return StripeProvider()

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="whsec_test")
    def test_forged_event_is_rejected(self):
        body = (b'{"type":"checkout.session.completed","data":{"object":'
                b'{"payment_status":"paid","client_reference_id":"INV-FORGE"}}}')
        with self.assertRaises(WebhookVerificationError):
            self._prov().parse_webhook(body=body, headers={"Stripe-Signature": "t=1,v1=deadbeef"})

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="")
    def test_missing_secret_fails_closed(self):
        body = b'{"type":"checkout.session.completed","data":{"object":{"payment_status":"paid"}}}'
        with self.assertRaises(WebhookVerificationError):
            self._prov().parse_webhook(body=body, headers={"Stripe-Signature": "t=1,v1=abc"})

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="whsec_test")
    def test_valid_signature_accepted(self):
        import hashlib
        import hmac
        import time

        body = (b'{"type":"checkout.session.completed","data":{"object":'
                b'{"payment_status":"paid","client_reference_id":"INV-OK","id":"cs_1"}}}')
        t = str(int(time.time()))
        sig = hmac.new(b"whsec_test", t.encode() + b"." + body, hashlib.sha256).hexdigest()
        event = self._prov().parse_webhook(body=body, headers={"Stripe-Signature": f"t={t},v1={sig}"})
        self.assertTrue(event.paid)
        self.assertEqual(event.invoice_number, "INV-OK")


_HP = dict(HYPERPAY_ENTITY_ID="8ac7a4c7", HYPERPAY_ACCESS_TOKEN="tok_test",
           HYPERPAY_WEBHOOK_SECRET="00" * 32, HYPERPAY_ENV="test",
           PAYMENT_PROVIDER="hyperpay")


class HyperPayTests(SimpleTestCase):
    def _prov(self):
        from platform.tenant.payments import HyperPayProvider
        return HyperPayProvider()

    def test_unconfigured_fails_loud(self):
        from platform.tenant.payments import PaymentProviderNotConfigured
        with override_settings(HYPERPAY_ENTITY_ID="", HYPERPAY_ACCESS_TOKEN=""):
            with self.assertRaises(PaymentProviderNotConfigured):
                self._prov()

    @override_settings(**_HP)
    def test_create_checkout_calls_oppwa_and_returns_widget_session(self):
        import httpx

        captured = {}

        def _fake_post(url, **kw):
            captured["url"] = url
            captured["data"] = kw.get("data")
            return httpx.Response(200, json={"id": "checkout_123", "result": {"code": "000.200.100"}},
                                  request=httpx.Request("POST", url))

        with mock.patch("httpx.post", _fake_post):
            inv = _FakeInvoice(invoice_number="INV-HP", amount=Decimal("149.00"), currency="SAR")
            session = self._prov().create_checkout(inv).as_dict()

        assert captured["url"] == "https://test.oppwa.com/v1/checkouts"
        assert captured["data"]["merchantTransactionId"] == "INV-HP"
        assert captured["data"]["amount"] == "149.00"
        assert session["mode"] == "hyperpay_widget"
        assert session["client_secret"] == "checkout_123"

    @override_settings(**_HP)
    def test_webhook_missing_headers_rejected(self):
        with self.assertRaises(WebhookVerificationError):
            self._prov().parse_webhook(body=b"x", headers={})

    @override_settings(HYPERPAY_ENTITY_ID="e", HYPERPAY_ACCESS_TOKEN="t", HYPERPAY_WEBHOOK_SECRET="")
    def test_webhook_missing_secret_fails_closed(self):
        with self.assertRaises(WebhookVerificationError):
            self._prov().parse_webhook(
                body=b"x", headers={"X-Initialization-Vector": "00", "X-Authentication-Tag": "00"}
            )

    @override_settings(**_HP)
    def test_webhook_decrypts_authenticated_payload(self):
        import binascii
        import json as _json

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = b"\x00" * 32
        iv = b"\x11" * 12
        plaintext = _json.dumps({
            "payload": {"merchantTransactionId": "INV-HP", "id": "8ac_pay_1",
                        "result": {"code": "000.100.110"}}
        }).encode()
        blob = AESGCM(key).encrypt(iv, plaintext, None)
        ct, tag = blob[:-16], blob[-16:]

        event = self._prov().parse_webhook(body=ct, headers={
            "X-Initialization-Vector": binascii.hexlify(iv).decode(),
            "X-Authentication-Tag": binascii.hexlify(tag).decode(),
        })
        assert event.paid is True
        assert event.invoice_number == "INV-HP"
        assert event.provider_ref == "8ac_pay_1"

    @override_settings(**_HP)
    def test_webhook_tampered_ciphertext_rejected(self):
        import binascii

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = b"\x00" * 32
        iv = b"\x11" * 12
        blob = AESGCM(key).encrypt(iv, b'{"x":1}', None)
        ct, tag = blob[:-16], blob[-16:]
        with self.assertRaises(WebhookVerificationError):
            self._prov().parse_webhook(body=ct + b"tamper", headers={
                "X-Initialization-Vector": binascii.hexlify(iv).decode(),
                "X-Authentication-Tag": binascii.hexlify(tag).decode(),
            })


class _FakeInvoice:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class PaymentVerifyViewTests(TestCase):
    """POST /api/v1/tenants/payments/verify/<provider>/ — the redirect-return
    path. A verified 'paid' result must activate the tenant; anything else
    must not."""

    def _url(self):
        from django.urls import reverse
        return reverse("tenant-payment-verify", args=["hyperpay"])

    @override_settings(**_HP)
    def test_paid_result_activates_tenant(self):
        from platform.tenant.payments import HyperPayProvider, PaymentEvent

        tenant, _, inv = _make_invoice(provider="hyperpay")

        def _paid(self, checkout_id):
            return PaymentEvent(provider="hyperpay", invoice_number=inv.invoice_number,
                                paid=True, provider_ref="8ac_ok")

        with mock.patch.object(HyperPayProvider, "verify_payment", _paid):
            resp = self.client.post(self._url(), {"checkout_id": "chk_1"})

        assert resp.status_code == 200, resp.content
        assert resp.json()["status"] == "active"
        tenant.refresh_from_db()
        assert tenant.status == TenantStatus.ACTIVE
        inv.refresh_from_db()
        assert inv.status == InvoiceStatus.PAID

    @override_settings(**_HP)
    def test_unpaid_result_does_not_activate(self):
        from platform.tenant.payments import HyperPayProvider, PaymentEvent

        tenant, _, inv = _make_invoice(provider="hyperpay")

        def _pending(self, checkout_id):
            return PaymentEvent(provider="hyperpay", invoice_number=inv.invoice_number, paid=False)

        with mock.patch.object(HyperPayProvider, "verify_payment", _pending):
            resp = self.client.post(self._url(), {"checkout_id": "chk_1"})

        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"
        tenant.refresh_from_db()
        assert tenant.status != TenantStatus.ACTIVE
