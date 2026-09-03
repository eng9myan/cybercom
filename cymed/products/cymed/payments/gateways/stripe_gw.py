"""Stripe gateway — fallback / international. Requires 'stripe' pip package (optional)."""
import os
from decimal import Decimal
from .base import BaseGateway, ChargeResult, RefundResult, WebhookEvent


class StripeGateway(BaseGateway):
    name = "stripe"
    supports = ["card", "apple_pay", "google_pay"]

    def __init__(self):
        self.api_key = os.environ.get("STRIPE_API_KEY", "")
        self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    def _client(self):
        try:
            import stripe
        except ImportError as e:
            raise RuntimeError("stripe package not installed; pip install stripe") from e
        stripe.api_key = self.api_key
        return stripe

    def tokenize(self, payload: dict) -> str:
        # Frontend collects card via Stripe Elements → returns payment_method id.
        # This function just validates and returns the id we received.
        return payload["payment_method_id"]

    def charge(
        self,
        token: str,
        amount: Decimal,
        currency: str,
        metadata: dict,
        *,
        idempotency_key: str | None = None,
        tenant_id: str | None = None,
    ) -> ChargeResult:
        stripe = self._client()
        md = dict(metadata or {})
        if tenant_id:
            md.setdefault("tenant_id", tenant_id)
        kwargs: dict = {
            "amount": int(amount * 100),                    # Stripe uses smallest unit
            "currency": currency.lower(),
            "payment_method": token,
            "confirm": True,
            "off_session": True,
            "metadata": md,
        }
        request_options: dict = {}
        if idempotency_key:
            request_options["idempotency_key"] = idempotency_key
        try:
            pi = stripe.PaymentIntent.create(**kwargs, **request_options)
            success = pi.status == "succeeded"
            return ChargeResult(
                success=success,
                gateway_reference=pi.id,
                status="succeeded" if success else "pending",
                raw=pi.to_dict_recursive(),
            )
        except Exception as exc:  # noqa: BLE001
            return ChargeResult(success=False, gateway_reference="",
                                status="failed", error_message=str(exc))

    def refund(
        self,
        gateway_ref: str,
        amount: Decimal | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> RefundResult:
        stripe = self._client()
        kwargs = {"payment_intent": gateway_ref}
        if amount is not None:
            kwargs["amount"] = int(amount * 100)
        request_options: dict = {}
        if idempotency_key:
            request_options["idempotency_key"] = idempotency_key
        r = stripe.Refund.create(**kwargs, **request_options)
        return RefundResult(success=r.status == "succeeded",
                             gateway_reference=r.id, raw=r.to_dict_recursive())

    def webhook_verify(self, headers: dict, body: bytes) -> bool:
        stripe = self._client()
        try:
            stripe.Webhook.construct_event(body, headers.get("Stripe-Signature", ""),
                                            self.webhook_secret)
            return True
        except Exception:
            return False

    def webhook_parse(self, body: bytes) -> WebhookEvent:
        import json
        data = json.loads(body.decode())
        return WebhookEvent(
            event_type=data.get("type", ""),
            gateway_reference=(data.get("data", {}).get("object") or {}).get("id", ""),
            raw=data,
        )
