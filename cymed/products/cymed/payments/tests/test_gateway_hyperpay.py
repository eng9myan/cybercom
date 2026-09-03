from __future__ import annotations

import hashlib
import hmac

import pytest


def _sign(secret: bytes, body: bytes) -> str:
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_webhook_verify_accepts_valid_hmac_sha256_signature(monkeypatch):
    monkeypatch.setenv("HYPERPAY_WEBHOOK_SECRET", "s3cr3t-shared-key")
    from products.cymed.payments.gateways.hyperpay import HyperPayGateway

    gw = HyperPayGateway()
    body = b'{"type":"payment.succeeded","payload":{"id":"gw_ref_1"}}'
    good_signature = _sign(b"s3cr3t-shared-key", body)

    assert gw.webhook_verify({"X-Webhook-Signature": good_signature}, body) is True


def test_webhook_verify_rejects_tampered_body(monkeypatch):
    monkeypatch.setenv("HYPERPAY_WEBHOOK_SECRET", "s3cr3t-shared-key")
    from products.cymed.payments.gateways.hyperpay import HyperPayGateway

    gw = HyperPayGateway()
    original_body = b'{"type":"payment.succeeded","payload":{"id":"gw_ref_1"}}'
    signature_for_original = _sign(b"s3cr3t-shared-key", original_body)

    tampered_body = b'{"type":"payment.succeeded","payload":{"id":"attacker_ref"}}'
    assert (
        gw.webhook_verify({"X-Webhook-Signature": signature_for_original}, tampered_body)
        is False
    )


def test_webhook_verify_rejects_missing_signature_header(monkeypatch):
    monkeypatch.setenv("HYPERPAY_WEBHOOK_SECRET", "s3cr3t-shared-key")
    from products.cymed.payments.gateways.hyperpay import HyperPayGateway

    gw = HyperPayGateway()
    body = b'{"type":"payment.succeeded"}'
    assert gw.webhook_verify({}, body) is False


def test_webhook_verify_rejects_when_secret_unconfigured(monkeypatch):
    monkeypatch.delenv("HYPERPAY_WEBHOOK_SECRET", raising=False)
    from products.cymed.payments.gateways.hyperpay import HyperPayGateway

    gw = HyperPayGateway()
    body = b'{"type":"payment.succeeded"}'
    # Even with a well-formed signature, an unconfigured secret must not verify.
    sig = _sign(b"", body)
    assert gw.webhook_verify({"X-Webhook-Signature": sig}, body) is False


def test_webhook_parse_extracts_type_and_reference(monkeypatch):
    monkeypatch.setenv("HYPERPAY_WEBHOOK_SECRET", "s3cr3t")
    from products.cymed.payments.gateways.hyperpay import HyperPayGateway

    gw = HyperPayGateway()
    body = b'{"type":"payment.succeeded","payload":{"id":"hp_evt_123"}}'
    event = gw.webhook_parse(body)

    assert event.event_type == "payment.succeeded"
    assert event.gateway_reference == "hp_evt_123"
    assert event.raw["payload"]["id"] == "hp_evt_123"
