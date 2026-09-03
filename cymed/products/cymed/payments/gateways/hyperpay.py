"""HyperPay gateway (COPYandPay / OPPWA).

Sandbox: https://eu-test.oppwa.com
Prod:    https://eu-prod.oppwa.com  (or the region your merchant is on)

Env vars
--------
HYPERPAY_BASE_URL         Full origin, no trailing slash. Defaults to sandbox.
HYPERPAY_ACCESS_TOKEN     OAuth bearer token issued by HyperPay.
HYPERPAY_ENTITY_ID        Channel/entity id (per brand/currency).
HYPERPAY_WEBHOOK_SECRET   Shared secret used to HMAC-SHA256 raw webhook bodies.

Docs
----
- Checkout create:   POST /v1/checkouts
- Checkout status:   GET  /v1/checkouts/{id}/payment
- Refund / capture:  POST /v1/payments/{paymentId}
- Registrations:     POST /v1/registrations                 (tokenise)
                     POST /v1/registrations/{token}/payments (charge saved token)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from .base import BaseGateway, ChargeResult, RefundResult, WebhookEvent

logger = logging.getLogger("cymed.payments.hyperpay")

DEFAULT_BASE_URL = "https://eu-test.oppwa.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 2

# HyperPay result codes considered a success.
# See: https://hyperpay.docs.oppwa.com/reference/resultCodes
_SUCCESS_PREFIXES = ("000.000.", "000.100.1", "000.300.", "000.400.0", "000.400.1")

# Brand aliases accepted by the caller → the value HyperPay expects.
_BRAND_MAP = {
    "visa": "VISA",
    "mastercard": "MASTER",
    "master": "MASTER",
    "mc": "MASTER",
    "mada": "MADA",
    "amex": "AMEX",
    "applepay": "APPLEPAY",
    "apple_pay": "APPLEPAY",
    "stcpay": "STC_PAY",
    "stc_pay": "STC_PAY",
}


@dataclass
class CheckoutSession:
    """Result of POST /v1/checkouts — hand `id` to the front-end widget."""

    id: str
    raw: dict[str, Any]


def _is_success_code(code: str) -> bool:
    return any(code.startswith(p) for p in _SUCCESS_PREFIXES)


def _normalise_brand(brand: str | None) -> str:
    if not brand:
        return "VISA"
    return _BRAND_MAP.get(brand.strip().lower(), brand.strip().upper())


class HyperPayGateway(BaseGateway):
    """Real (sandbox-capable) HyperPay integration.

    All I/O funnels through `_request`, which is injectable via `client=` so
    tests can pass a mock httpx.Client without patching module globals.
    """

    name = "hyperpay"
    supports = ["card", "apple_pay", "stc_pay", "mada"]

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.base_url = os.getenv("HYPERPAY_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        self.entity_id = os.getenv("HYPERPAY_ENTITY_ID", "")
        self.access_token = os.getenv("HYPERPAY_ACCESS_TOKEN", "")
        self.webhook_secret = os.getenv("HYPERPAY_WEBHOOK_SECRET", "").encode()
        self._owned_client = client is None
        self._client = client or self._build_client()

    # ────────────────────────────── plumbing ──────────────────────────────

    def _build_client(self) -> httpx.Client:
        """Build an httpx.Client with retries limited to network errors.

        `httpx.HTTPTransport(retries=N)` retries on connection errors only
        (ConnectError, ConnectTimeout) — never on a completed 4xx/5xx.
        """
        transport = httpx.HTTPTransport(retries=DEFAULT_RETRIES)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        return httpx.Client(
            base_url=self.base_url,
            timeout=DEFAULT_TIMEOUT,
            headers=headers,
            transport=transport,
        )

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> "HyperPayGateway":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def _log(self, level: int, event: str, **fields: Any) -> None:
        # Never log auth or PAN. Log method/endpoint/status/id, that's it.
        logger.log(level, event, extra={"hyperpay": fields})

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        """Execute a call. Raises httpx.HTTPStatusError on 4xx/5xx.

        `data` is form-encoded (HyperPay's server-to-server API takes
        application/x-www-form-urlencoded, not JSON).
        """
        headers: dict[str, str] = {}
        if idempotency_key:
            # HyperPay does not have a formal Idempotency-Key header on all
            # endpoints, but merchantTransactionId is the customer-side
            # dedup token; we still send the header so any downstream proxy
            # (or a future HyperPay change) can honour it.
            headers["Idempotency-Key"] = idempotency_key
            if data is not None and "merchantTransactionId" not in data:
                data = {**data, "merchantTransactionId": idempotency_key}

        self._log(
            logging.INFO,
            "hyperpay.request",
            method=method,
            path=path,
            idempotency_key=idempotency_key,
        )

        try:
            response = self._client.request(method, path, data=data, headers=headers)
        except httpx.HTTPError as exc:
            # Network / timeout / decode error — real failure, do not swallow.
            self._log(
                logging.ERROR,
                "hyperpay.transport_error",
                method=method,
                path=path,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

        self._log(
            logging.INFO,
            "hyperpay.response",
            method=method,
            path=path,
            status=response.status_code,
        )

        # 4xx/5xx: raise, do NOT retry (retries live in the transport for
        # network errors only). The caller decides how to surface it.
        response.raise_for_status()
        return response

    def _base_form(self) -> dict[str, str]:
        if not self.entity_id:
            raise RuntimeError("HYPERPAY_ENTITY_ID not configured")
        return {"entityId": self.entity_id}

    # ─────────────────────────── checkout flow ────────────────────────────

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        *,
        brand: str = "VISA",
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutSession:
        """POST /v1/checkouts — returns a checkout id for the front-end widget."""
        meta = metadata or {}
        data = self._base_form()
        data.update(
            {
                "amount": f"{Decimal(amount):.2f}",
                "currency": currency,
                "paymentType": "DB",
                "paymentBrand": _normalise_brand(brand),
            }
        )
        if "bill_number" in meta:
            data["merchantTransactionId"] = str(meta["bill_number"])
        if "customer_email" in meta:
            data["customer.email"] = str(meta["customer_email"])

        resp = self._request(
            "POST", "/v1/checkouts", data=data, idempotency_key=idempotency_key
        )
        body = resp.json()
        checkout_id = body.get("id", "")
        self._log(
            logging.INFO,
            "hyperpay.checkout_created",
            checkout_id=checkout_id,
            amount=str(amount),
            currency=currency,
        )
        return CheckoutSession(id=checkout_id, raw=body)

    def get_checkout_status(self, checkout_id: str) -> ChargeResult:
        """GET /v1/checkouts/{id}/payment — poll after the widget completes."""
        if not self.entity_id:
            raise RuntimeError("HYPERPAY_ENTITY_ID not configured")
        # HyperPay requires entityId on the GET as a query param.
        path = f"/v1/checkouts/{checkout_id}/payment"
        resp = self._client.get(path, params={"entityId": self.entity_id})
        self._log(
            logging.INFO,
            "hyperpay.checkout_status",
            checkout_id=checkout_id,
            status=resp.status_code,
        )
        resp.raise_for_status()
        body = resp.json()
        return self._charge_result_from_body(body)

    # ──────────────────────────── tokenise ────────────────────────────────

    def tokenize(self, payload: dict) -> str:
        """POST /v1/registrations — returns a registration (token) id.

        In production, do NOT send raw PAN through your own backend. Use
        HyperPay's hosted COPYandPay widget with `createRegistration=true`
        and hand the resulting registration id off to this class. This code
        path exists so server-to-server tests still work in the sandbox.
        """
        data = self._base_form()
        data["paymentBrand"] = _normalise_brand(payload.get("brand"))
        # Card + holder details (sandbox use). Callers passing a
        # pre-tokenised id should just return it and not call this.
        for src, dst in (
            ("card_number", "card.number"),
            ("holder", "card.holder"),
            ("expiry_month", "card.expiryMonth"),
            ("expiry_year", "card.expiryYear"),
            ("cvv", "card.cvv"),
        ):
            if src in payload:
                data[dst] = str(payload[src])

        resp = self._request(
            "POST",
            "/v1/registrations",
            data=data,
            idempotency_key=payload.get("idempotency_key"),
        )
        body = resp.json()
        code = body.get("result", {}).get("code", "")
        if not _is_success_code(code):
            raise RuntimeError(
                f"HyperPay tokenize failed: {code} "
                f"{body.get('result', {}).get('description', '')}"
            )
        token = body.get("id", "")
        self._log(logging.INFO, "hyperpay.tokenized", token=token)
        return token

    # ───────────────────────────── charge ─────────────────────────────────

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
        """Debit against a stored registration (token).

        Path: POST /v1/registrations/{token}/payments  (paymentType=DB).

        `idempotency_key` and `tenant_id` are additive kwargs (backward
        compatible with the ABC). `tenant_id` is folded into
        merchantTransactionId when both are present.
        """
        if not token:
            raise ValueError("HyperPay charge requires a registration token id")

        meta = metadata or {}
        data = self._base_form()
        data.update(
            {
                "amount": f"{Decimal(amount):.2f}",
                "currency": currency,
                "paymentType": "DB",
                "recurringType": "REPEATED",
                "paymentBrand": _normalise_brand(meta.get("brand")),
            }
        )
        if "bill_number" in meta and "merchantTransactionId" not in data:
            data["merchantTransactionId"] = str(meta["bill_number"])
        if tenant_id:
            # Cheap tenant tag surviving through the gateway → useful when
            # matching webhooks back to a tenant.
            data["customParameters[tenantId]"] = str(tenant_id)

        self._log(
            logging.INFO,
            "hyperpay.charge_begin",
            token=token,
            amount=str(amount),
            currency=currency,
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
        )
        resp = self._request(
            "POST",
            f"/v1/registrations/{token}/payments",
            data=data,
            idempotency_key=idempotency_key,
        )
        body = resp.json()
        result = self._charge_result_from_body(body)
        self._log(
            logging.INFO,
            "hyperpay.charge_done",
            transaction_id=result.gateway_reference,
            status=result.status,
            success=result.success,
        )
        return result

    def _charge_result_from_body(self, body: dict[str, Any]) -> ChargeResult:
        code = body.get("result", {}).get("code", "")
        success = _is_success_code(code)
        return ChargeResult(
            success=success,
            gateway_reference=body.get("id", ""),
            status="succeeded" if success else "failed",
            raw=body,
            error_message=(
                "" if success else body.get("result", {}).get("description", "")
            ),
        )

    # ───────────────────────────── refund ─────────────────────────────────

    def refund(
        self,
        gateway_ref: str,
        amount: Decimal | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> RefundResult:
        """POST /v1/payments/{transaction_id}  paymentType=RF."""
        if not gateway_ref:
            raise ValueError("HyperPay refund requires a transaction id")
        data = self._base_form()
        data["paymentType"] = "RF"
        if amount is not None:
            data["amount"] = f"{Decimal(amount):.2f}"

        resp = self._request(
            "POST",
            f"/v1/payments/{gateway_ref}",
            data=data,
            idempotency_key=idempotency_key,
        )
        body = resp.json()
        code = body.get("result", {}).get("code", "")
        success = _is_success_code(code)
        self._log(
            logging.INFO,
            "hyperpay.refund_done",
            original=gateway_ref,
            refund_id=body.get("id", ""),
            success=success,
        )
        return RefundResult(
            success=success,
            gateway_reference=body.get("id", gateway_ref),
            raw=body,
        )

    # ──────────────────────────── webhooks ────────────────────────────────

    def webhook_verify(self, headers: dict, body: bytes) -> bool:
        """Constant-time HMAC-SHA256 check on the raw request body.

        HyperPay signs webhooks; the header name varies by deployment. We
        accept both `X-Signature` (spec-preferred) and `X-Webhook-Signature`
        (existing callers).
        """
        signature = (
            headers.get("X-Signature")
            or headers.get("x-signature")
            or headers.get("X-Webhook-Signature")
            or headers.get("x-webhook-signature")
            or ""
        )
        if not self.webhook_secret or not signature:
            self._log(
                logging.WARNING,
                "hyperpay.webhook_missing_signature_or_secret",
                have_secret=bool(self.webhook_secret),
                have_signature=bool(signature),
            )
            return False
        expected = hmac.new(self.webhook_secret, body, hashlib.sha256).hexdigest()
        ok = hmac.compare_digest(expected, signature)
        if not ok:
            self._log(logging.WARNING, "hyperpay.webhook_signature_mismatch")
        return ok

    def webhook_parse(self, body: bytes) -> WebhookEvent:
        data = json.loads(body.decode("utf-8"))
        payload = data.get("payload") or {}
        return WebhookEvent(
            event_type=data.get("type", ""),
            gateway_reference=payload.get("id", data.get("id", "")),
            raw=data,
        )
