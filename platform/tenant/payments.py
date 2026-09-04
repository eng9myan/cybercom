"""
Provider-agnostic online-payment seam for self-serve subscriptions.

Standing product decision: the concrete gateway (Stripe / Paddle / HyperPay)
is chosen later. Until then everything is wired against this abstraction so the
frontend, the register endpoint, and the webhook already speak one shape and
swapping in a real provider is a config change, not a rewrite.

Selection: settings.PAYMENT_PROVIDER (env CYCOM_PAYMENT_PROVIDER), default
"manual". Providers:

  * manual   — bank transfer. No online charge; finance confirms and the
               subscription activates. Always available, no keys.
  * fake     — DEBUG-only. Simulates a hosted-checkout redirect + a webhook
               that always confirms. Lets the whole online-payment path be
               exercised end-to-end with no external account. Refuses to load
               unless settings.DEBUG.
  * stripe   — reference real integration (Stripe Checkout Session). Raises
               PaymentProviderNotConfigured until STRIPE_SECRET_KEY is set.
  * paddle / hyperpay — seams with the same contract, guarded the same way;
               fill the create_checkout body when that account exists.

A provider never activates anything itself. It only (a) starts a checkout for
an invoice and (b) turns an inbound webhook into a normalized PaymentEvent.
Activation is the caller's job (activate_paid_subscription in services.py), so
the manual and online paths converge on exactly one activation code path.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from decimal import Decimal

from django.conf import settings


class PaymentError(Exception):
    """Base for payment-seam failures."""


class PaymentProviderNotConfigured(PaymentError):
    """Selected provider is missing its credentials/config."""


class WebhookVerificationError(PaymentError):
    """Inbound webhook failed signature/authenticity verification."""


@dataclass
class CheckoutSession:
    """What the register endpoint hands back to the frontend.

    mode drives the UI:
      "manual"        -> show bank-transfer instructions, no redirect.
      "redirect"      -> send the browser to `url` (hosted checkout).
      "client_secret" -> mount the provider's embedded element with `client_secret`.
    """

    provider: str
    mode: str
    reference: str = ""
    url: str = ""
    client_secret: str = ""
    publishable_key: str = ""
    instructions: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = {"provider": self.provider, "mode": self.mode, "reference": self.reference}
        if self.url:
            d["url"] = self.url
        if self.client_secret:
            d["client_secret"] = self.client_secret
        if self.publishable_key:
            d["publishable_key"] = self.publishable_key
        if self.instructions:
            d["instructions"] = self.instructions
        return d


@dataclass
class PaymentEvent:
    """Normalized inbound webhook event."""

    provider: str
    invoice_number: str
    paid: bool
    provider_ref: str = ""
    raw: dict = field(default_factory=dict)


class PaymentProvider:
    code = "base"

    def create_checkout(self, invoice, *, success_url: str = "", cancel_url: str = "") -> CheckoutSession:
        raise NotImplementedError

    def parse_webhook(self, *, body: bytes, headers: dict) -> PaymentEvent:
        raise NotImplementedError


class ManualBankTransferProvider(PaymentProvider):
    code = "manual"

    def create_checkout(self, invoice, *, success_url: str = "", cancel_url: str = "") -> CheckoutSession:
        bank = getattr(settings, "BANK_TRANSFER_DETAILS", {}) or {
            "beneficiary": "CyberCom",
            "note": "Bank details are configured by finance (settings.BANK_TRANSFER_DETAILS).",
        }
        return CheckoutSession(
            provider=self.code,
            mode="manual",
            reference=invoice.invoice_number,
            instructions={
                **bank,
                "amount": str(invoice.amount),
                "currency": invoice.currency,
                "reference": invoice.invoice_number,
                "due_date": invoice.due_date.isoformat(),
            },
        )

    def parse_webhook(self, *, body: bytes, headers: dict) -> PaymentEvent:
        # Manual has no webhook — confirmation is a finance action.
        raise WebhookVerificationError("manual provider has no webhook")


class FakeProvider(PaymentProvider):
    """DEBUG-only simulator of a hosted-checkout gateway."""

    code = "fake"

    def __init__(self):
        if not settings.DEBUG:
            raise PaymentProviderNotConfigured("fake payment provider is DEBUG-only")

    @staticmethod
    def _secret() -> bytes:
        return (getattr(settings, "FAKE_PAYMENT_SECRET", "") or "fake-payment-secret").encode()

    def create_checkout(self, invoice, *, success_url: str = "", cancel_url: str = "") -> CheckoutSession:
        # A real gateway would return its hosted URL; we point at our own
        # simulate endpoint so the full redirect+webhook loop can be tested.
        return CheckoutSession(
            provider=self.code,
            mode="redirect",
            reference=invoice.invoice_number,
            url=f"/api/v1/tenants/payments/simulate/?invoice={invoice.invoice_number}",
        )

    def sign(self, invoice_number: str) -> str:
        return hmac.new(self._secret(), invoice_number.encode(), hashlib.sha256).hexdigest()

    def parse_webhook(self, *, body: bytes, headers: dict) -> PaymentEvent:
        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise WebhookVerificationError("invalid JSON") from exc
        inv = payload.get("invoice_number", "")
        sig = headers.get("X-Fake-Signature", "")
        if not inv or not hmac.compare_digest(sig, self.sign(inv)):
            raise WebhookVerificationError("bad fake signature")
        return PaymentEvent(
            provider=self.code,
            invoice_number=inv,
            paid=payload.get("status") == "paid",
            provider_ref=payload.get("ref", ""),
            raw=payload,
        )


class StripeProvider(PaymentProvider):
    """Reference real integration (Stripe Checkout Session).

    Enabled the moment STRIPE_SECRET_KEY is present. No code change needed to
    go live — this is the shape a chosen provider fills.
    """

    code = "stripe"

    def __init__(self):
        self.secret_key = getattr(settings, "STRIPE_SECRET_KEY", "") or ""
        self.publishable_key = getattr(settings, "STRIPE_PUBLISHABLE_KEY", "") or ""
        self.webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""
        if not self.secret_key:
            raise PaymentProviderNotConfigured(
                "StripeProvider requires settings.STRIPE_SECRET_KEY. Set it (and "
                "STRIPE_PUBLISHABLE_KEY / STRIPE_WEBHOOK_SECRET) once the Stripe "
                "account exists, then set CYCOM_PAYMENT_PROVIDER=stripe."
            )

    def create_checkout(self, invoice, *, success_url: str = "", cancel_url: str = "") -> CheckoutSession:
        import httpx  # lazy: only needed when Stripe is actually selected

        # Stripe wants the smallest currency unit (fils/halala/cents). All the
        # currencies we price in are 2-decimal, so *100.
        minor = int((Decimal(invoice.amount) * 100).to_integral_value())
        resp = httpx.post(
            "https://api.stripe.com/v1/checkout/sessions",
            auth=(self.secret_key, ""),
            data={
                "mode": "subscription" if invoice.subscription.auto_renew else "payment",
                "success_url": success_url or "https://www.cy-com.com/onboarding?paid=1",
                "cancel_url": cancel_url or "https://www.cy-com.com/pricing",
                "client_reference_id": invoice.invoice_number,
                "line_items[0][price_data][currency]": invoice.currency.lower(),
                "line_items[0][price_data][product_data][name]": f"Subscription {invoice.invoice_number}",
                "line_items[0][price_data][unit_amount]": str(minor),
                "line_items[0][price_data][recurring][interval]": "month",
                "line_items[0][quantity]": "1",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return CheckoutSession(
            provider=self.code,
            mode="redirect",
            reference=invoice.invoice_number,
            url=data.get("url", ""),
            publishable_key=self.publishable_key,
        )

    # Reject webhook events whose signature timestamp is older than this
    # (replay protection). Matches Stripe's own default tolerance.
    _SIGNATURE_TOLERANCE_SECONDS = 300

    def _verify_signature(self, body: bytes, sig_header: str) -> None:
        """Real Stripe webhook verification (HMAC-SHA256 over `{t}.{payload}`),
        fail-closed. Equivalent to stripe.Webhook.construct_event without the
        SDK dependency. A missing secret or bad signature is a hard reject —
        never treat an unverified event as paid."""
        import hashlib
        import hmac
        import time

        if not self.webhook_secret:
            raise WebhookVerificationError(
                "STRIPE_WEBHOOK_SECRET is not set — refusing to trust an unverified webhook"
            )
        parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
        timestamp, v1 = parts.get("t"), parts.get("v1")
        if not timestamp or not v1:
            raise WebhookVerificationError("malformed Stripe-Signature header")
        try:
            age = abs(time.time() - int(timestamp))
        except ValueError as exc:
            raise WebhookVerificationError("invalid Stripe-Signature timestamp") from exc
        if age > self._SIGNATURE_TOLERANCE_SECONDS:
            raise WebhookVerificationError("Stripe-Signature timestamp outside tolerance (replay?)")
        signed_payload = timestamp.encode() + b"." + (body or b"")
        expected = hmac.new(self.webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, v1):
            raise WebhookVerificationError("Stripe-Signature verification failed")

    def parse_webhook(self, *, body: bytes, headers: dict) -> PaymentEvent:
        # Fail-closed signature verification is mandatory: a forged "paid" event
        # would otherwise activate any tenant for free (invoice_number is handed
        # to the public registrant). See _verify_signature.
        self._verify_signature(body, headers.get("Stripe-Signature", ""))
        try:
            event = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise WebhookVerificationError("invalid JSON") from exc
        obj = event.get("data", {}).get("object", {})
        paid = event.get("type") in ("checkout.session.completed", "invoice.paid") and (
            obj.get("payment_status") == "paid" or obj.get("status") == "paid"
        )
        return PaymentEvent(
            provider=self.code,
            invoice_number=obj.get("client_reference_id", ""),
            paid=paid,
            provider_ref=obj.get("id", ""),
            raw=event,
        )


class _UnconfiguredProvider(PaymentProvider):
    """Paddle / HyperPay seam — same contract, body filled when the account
    exists. Kept explicit (not deleted) so selecting it fails loud and clear
    rather than silently falling back to another gateway."""

    def __init__(self):
        raise PaymentProviderNotConfigured(
            f"{self.code} is not configured yet. Provide its credentials and "
            f"implement create_checkout/parse_webhook, or choose another "
            f"CYCOM_PAYMENT_PROVIDER."
        )


class PaddleProvider(_UnconfiguredProvider):
    code = "paddle"


class HyperPayProvider(PaymentProvider):
    """HyperPay / OPPWA (COPYandPAY) — the recommended first regional gateway
    (JO + SA + UAE coverage, mada/KNET/benefit, tokenisation).

    Enabled the moment HYPERPAY_ENTITY_ID + HYPERPAY_ACCESS_TOKEN are set.
      HYPERPAY_ENV            "test" (default) -> test.oppwa.com | "live" -> oppwa.com
      HYPERPAY_ENTITY_ID      the channel entityId
      HYPERPAY_ACCESS_TOKEN   Bearer token for the API
      HYPERPAY_WEBHOOK_SECRET hex-encoded AES key for decrypting async notifications

    Flow: create_checkout() -> a checkout id; the frontend mounts the
    COPYandPAY widget with that id (mode="hyperpay_widget"). On return we call
    verify_payment(checkout_id). HyperPay also POSTs an encrypted webhook which
    parse_webhook() decrypts + authenticates (fail-closed).
    """

    code = "hyperpay"
    _SUCCESS_RE = r"^(000\.000\.|000\.100\.1|000\.[36]|000\.400\.0[^3]|000\.400\.100)"

    def __init__(self):
        self.entity_id = getattr(settings, "HYPERPAY_ENTITY_ID", "") or ""
        self.access_token = getattr(settings, "HYPERPAY_ACCESS_TOKEN", "") or ""
        self.webhook_secret = getattr(settings, "HYPERPAY_WEBHOOK_SECRET", "") or ""
        env = (getattr(settings, "HYPERPAY_ENV", "test") or "test").lower()
        self.base_url = "https://oppwa.com" if env == "live" else "https://test.oppwa.com"
        if not self.entity_id or not self.access_token:
            raise PaymentProviderNotConfigured(
                "HyperPayProvider requires settings.HYPERPAY_ENTITY_ID and "
                "HYPERPAY_ACCESS_TOKEN. Set them (and HYPERPAY_WEBHOOK_SECRET) once "
                "the HyperPay account exists, then set CYCOM_PAYMENT_PROVIDER=hyperpay."
            )

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    def create_checkout(self, invoice, *, success_url: str = "", cancel_url: str = "") -> CheckoutSession:
        import httpx  # lazy: only needed when HyperPay is actually selected

        amount = str(Decimal(invoice.amount).quantize(Decimal("0.01")))
        resp = httpx.post(
            f"{self.base_url}/v1/checkouts",
            headers=self._headers(),
            data={
                "entityId": self.entity_id,
                "amount": amount,
                "currency": invoice.currency.upper(),
                "paymentType": "DB",
                "merchantTransactionId": invoice.invoice_number,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        checkout_id = data.get("id", "")
        if not checkout_id:
            raise PaymentError(f"HyperPay did not return a checkout id: {data!r}")
        return CheckoutSession(
            provider=self.code,
            mode="hyperpay_widget",
            reference=invoice.invoice_number,
            client_secret=checkout_id,               # widget data-checkout-id
            url=f"{self.base_url}/v1/paymentWidgets.js?checkoutId={checkout_id}",
            instructions={"base_url": self.base_url},
        )

    def verify_payment(self, checkout_id: str) -> PaymentEvent:
        """Redirect-return path: query the payment result for a checkout id."""
        import re

        import httpx

        if not checkout_id:
            raise PaymentError("checkout_id is required")
        resp = httpx.get(
            f"{self.base_url}/v1/checkouts/{checkout_id}/payment",
            headers=self._headers(),
            params={"entityId": self.entity_id},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        code = (data.get("result", {}) or {}).get("code", "")
        return PaymentEvent(
            provider=self.code,
            invoice_number=data.get("merchantTransactionId", ""),
            paid=bool(re.match(self._SUCCESS_RE, code)),
            provider_ref=data.get("id", ""),
            raw=data,
        )

    def parse_webhook(self, *, body: bytes, headers: dict) -> PaymentEvent:
        """Decrypt + authenticate a HyperPay async notification (AES-256-GCM).

        The IV and auth tag arrive in headers; the body is the ciphertext. A
        missing key or a failed tag check is a hard reject — an unauthenticated
        'paid' event must never activate a tenant."""
        import binascii
        import re

        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if not self.webhook_secret:
            raise WebhookVerificationError(
                "HYPERPAY_WEBHOOK_SECRET is not set — refusing to trust an unverified webhook"
            )
        iv_hex = headers.get("X-Initialization-Vector", "")
        tag_hex = headers.get("X-Authentication-Tag", "")
        if not iv_hex or not tag_hex:
            raise WebhookVerificationError("missing HyperPay IV / auth-tag headers")
        try:
            key = binascii.unhexlify(self.webhook_secret)
            iv = binascii.unhexlify(iv_hex)
            tag = binascii.unhexlify(tag_hex)
            plaintext = AESGCM(key).decrypt(iv, (body or b"") + tag, None)
        except (binascii.Error, ValueError, InvalidTag) as exc:
            raise WebhookVerificationError(f"HyperPay webhook decryption failed: {exc}") from exc

        try:
            payload = json.loads(plaintext or b"{}")
        except json.JSONDecodeError as exc:
            raise WebhookVerificationError("decrypted HyperPay payload is not JSON") from exc

        p = payload.get("payload", payload)
        code = (p.get("result", {}) or {}).get("code", "")
        return PaymentEvent(
            provider=self.code,
            invoice_number=p.get("merchantTransactionId", ""),
            paid=bool(re.match(self._SUCCESS_RE, code)),
            provider_ref=p.get("id", ""),
            raw=payload,
        )


_REGISTRY = {
    "manual": ManualBankTransferProvider,
    "fake": FakeProvider,
    "stripe": StripeProvider,
    "paddle": PaddleProvider,
    "hyperpay": HyperPayProvider,
}


def get_payment_provider(code: str | None = None) -> PaymentProvider:
    code = (code or getattr(settings, "PAYMENT_PROVIDER", "manual") or "manual").lower()
    cls = _REGISTRY.get(code)
    if cls is None:
        raise PaymentProviderNotConfigured(f"unknown payment provider '{code}'")
    return cls()


def active_provider_code() -> str:
    return (getattr(settings, "PAYMENT_PROVIDER", "manual") or "manual").lower()
