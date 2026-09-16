"""
Payment orchestration: idempotent intent creation, capture, refund, webhook
application, and reconciliation onto the existing fee ledgers.

Reconciliation deliberately does not reimplement any accounting. It calls
`products.cyed.billing.services.record_payment` for installments and creates a
`cyed_fees.Payment` then calls the invoice's own `recalc_status()` — the same
two paths the finance UI already uses. This module's job is to decide *when*
money is real, not to redefine what a paid invoice means.
"""

import json
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.utils import timezone

from products.cyed.payments.models import (
    UNKNOWN_TENANT,
    PaymentIntent,
    Refund,
    WebhookEvent,
)
from products.cyed.payments.providers import (
    PaymentProviderError,
    ProviderNotConfigured,
    get_provider,
)

CENT = Decimal("0.01")

# Event types this webhook handler understands.
EVT_SUCCEEDED = "payment_intent.succeeded"
EVT_FAILED = "payment_intent.failed"
EVT_CANCELLED = "payment_intent.cancelled"
EVT_REFUNDED = "refund.succeeded"


class PaymentError(Exception):
    """A payment operation was refused for a business reason (→ HTTP 400)."""


def q(value) -> Decimal:
    try:
        return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PaymentError(f"'{value}' is not a valid monetary amount.") from exc


# ── creation ─────────────────────────────────────────────────────────────────
def create_intent(
    *,
    tenant_id,
    amount,
    idempotency_key: str,
    currency: str = "AUD",
    method: str = "card",
    provider: str | None = None,
    invoice=None,
    installment=None,
    payer_email: str = "",
    description: str = "",
    created_by: str = "",
    metadata: dict | None = None,
):
    """
    Create a payment intent, or return the existing one for this idempotency key.

    Returns (intent, created). `created` is False when an intent already existed
    — the caller must treat that as success, not as a conflict. This is the
    single most important property in the module: a parent whose phone drops
    mid-payment and retries must not be charged twice, and a provider that
    retries our own API call must not open a second charge.
    """
    key = (idempotency_key or "").strip()
    if not key:
        raise PaymentError("idempotency_key is required — it is what prevents double charging.")

    existing = PaymentIntent.objects.filter(tenant_id=tenant_id, idempotency_key=key).first()
    if existing is not None:
        return existing, False

    amount = q(amount)
    if amount <= 0:
        raise PaymentError("amount must be greater than zero.")
    if invoice is not None and installment is not None:
        raise PaymentError("An intent may target an invoice or an installment, not both.")

    adapter = get_provider(provider)  # raises ProviderNotConfigured — never silent

    try:
        with transaction.atomic():
            intent = PaymentIntent.objects.create(
                tenant_id=tenant_id,
                amount=amount,
                currency=(currency or "AUD").upper()[:3],
                method=method or "card",
                provider=adapter.name,
                idempotency_key=key,
                invoice=invoice,
                installment=installment,
                payer_email=payer_email or "",
                description=description or "",
                created_by=created_by or "",
                metadata=metadata or {},
                status="created",
            )
    except IntegrityError:
        # Lost a race with a concurrent request carrying the same key: the other
        # one won, so return its intent rather than erroring or double-charging.
        existing = PaymentIntent.objects.filter(tenant_id=tenant_id, idempotency_key=key).first()
        if existing is None:
            raise
        return existing, False

    try:
        result = adapter.authorize(intent)
    except PaymentProviderError:
        # The gateway could not be reached or is not configured. That is a
        # deployment fault, not a payment outcome, so the half-open intent must
        # not survive: its idempotency key is unique per tenant, and leaving the
        # row behind would make every retry return this stale `created` intent
        # — still unauthorised — even after the provider is fixed. Delete it so
        # the key is free, and let the error surface.
        intent.delete()
        raise

    if result.ok:
        intent.status = result.status or "pending"
        intent.provider_reference = result.reference or ""
        if result.raw:
            intent.metadata = {**(intent.metadata or {}), "authorize": result.raw}
    else:
        intent.status = "failed"
        intent.failure_reason = (result.failure_reason or "authorization_failed")[:255]
    intent.save(update_fields=["status", "provider_reference", "failure_reason", "metadata", "updated_at"])

    if intent.status == "succeeded":
        # A provider that authorises and captures in one step.
        _settle(intent, intent.amount)
    return intent, True


# ── capture / failure / cancellation ─────────────────────────────────────────
def capture_intent(intent: PaymentIntent, amount=None, actor: str = "") -> PaymentIntent:
    """
    Take the money. For the manual provider this is the finance officer
    confirming a BPAY/bank transfer actually landed.
    """
    if intent.status == "succeeded":
        # Idempotent: capturing an already-captured intent is a no-op, not an
        # error, so a retried request cannot take the money twice.
        return intent
    if intent.status in PaymentIntent.TERMINAL:
        raise PaymentError(f"A {intent.status} payment cannot be captured.")

    amount = q(amount) if amount is not None else q(intent.amount)
    if amount <= 0:
        raise PaymentError("Capture amount must be greater than zero.")
    if amount > q(intent.amount):
        raise PaymentError(
            f"Cannot capture {amount} — the intent is only authorised for {q(intent.amount)}."
        )

    adapter = get_provider(intent.provider)
    result = adapter.capture(intent, amount)
    if not result.ok:
        return mark_failed(intent, result.failure_reason or "capture_failed")

    if result.reference:
        intent.provider_reference = result.reference
    if actor and not intent.created_by:
        intent.created_by = actor
    _settle(intent, amount)
    return intent


def _settle(intent: PaymentIntent, amount: Decimal) -> PaymentIntent:
    """Mark an intent succeeded and push the money onto the fee ledger."""
    intent.status = "succeeded"
    intent.captured_amount = q(amount)
    intent.succeeded_at = intent.succeeded_at or timezone.now()
    intent.failure_reason = ""
    intent.save(update_fields=[
        "status", "captured_amount", "succeeded_at", "failure_reason",
        "provider_reference", "created_by", "updated_at",
    ])
    reconcile_intent(intent)
    return intent


def mark_failed(intent: PaymentIntent, reason: str = "") -> PaymentIntent:
    if intent.status == "succeeded":
        raise PaymentError("A captured payment cannot be marked failed; refund it instead.")
    if intent.status in PaymentIntent.TERMINAL:
        return intent
    intent.status = "failed"
    intent.failure_reason = (reason or "unknown")[:255]
    intent.save(update_fields=["status", "failure_reason", "updated_at"])
    return intent


def cancel_intent(intent: PaymentIntent, reason: str = "") -> PaymentIntent:
    if intent.status in PaymentIntent.TERMINAL:
        raise PaymentError(f"A {intent.status} payment cannot be cancelled.")
    intent.status = "cancelled"
    intent.failure_reason = (reason or "")[:255]
    intent.save(update_fields=["status", "failure_reason", "updated_at"])
    return intent


# ── refunds ──────────────────────────────────────────────────────────────────
def refund_intent(intent: PaymentIntent, amount=None, reason: str = "", actor: str = "") -> Refund:
    """
    Refund all or part of a captured intent.

    The total of all successful refunds can never exceed what was captured —
    checked here and backed by a DB CheckConstraint, because an over-refund is
    the school paying a parent money it never received.
    """
    if intent.status not in ("succeeded", "refunded"):
        raise PaymentError(f"Only a captured payment can be refunded (this one is {intent.status}).")

    available = q(intent.captured_amount) - q(intent.refunded_amount)
    amount = q(amount) if amount is not None else available
    if amount <= 0:
        raise PaymentError("Refund amount must be greater than zero.")
    if amount > available:
        raise PaymentError(
            f"Refund of {amount} exceeds the refundable balance of {available} "
            f"(captured {q(intent.captured_amount)}, already refunded {q(intent.refunded_amount)})."
        )

    adapter = get_provider(intent.provider)
    refund = Refund.objects.create(
        tenant_id=intent.tenant_id, intent=intent, amount=amount,
        reason=reason or "", created_by=actor or "", status="pending",
    )
    result = adapter.refund(intent, amount, reason)
    if not result.ok:
        refund.status = "failed"
        refund.failure_reason = (result.failure_reason or "refund_failed")[:255]
        refund.save(update_fields=["status", "failure_reason", "updated_at"])
        return refund

    refund.status = "succeeded"
    refund.provider_reference = result.reference or ""
    refund.save(update_fields=["status", "provider_reference", "updated_at"])

    intent.refunded_amount = q(Decimal(intent.refunded_amount) + amount)
    if intent.refunded_amount >= q(intent.captured_amount):
        intent.status = "refunded"
    intent.save(update_fields=["refunded_amount", "status", "updated_at"])

    _reverse_on_ledger(intent, refund)
    return refund


# ── reconciliation onto the existing fee ledgers ─────────────────────────────
def reconcile_intent(intent: PaymentIntent):
    """
    Write a captured intent onto its linked invoice/installment, exactly once.

    `reconciled_at` plus a reference lookup make this safe to call repeatedly —
    a replayed webhook, a retried capture and a manual re-run all converge on
    one ledger row.
    """
    if intent.status != "succeeded" or intent.reconciled_at is not None:
        return None
    amount = q(intent.captured_amount)
    if amount <= 0:
        return None

    ledger_row = None
    if intent.installment_id:
        from products.cyed.billing import services as billing_services
        from products.cyed.billing.models import InstallmentPayment

        if InstallmentPayment.objects.filter(
            tenant_id=intent.tenant_id, installment_id=intent.installment_id,
            reference=intent.ledger_reference,
        ).exists():
            ledger_row = "already-present"
        else:
            billing_services.record_payment(
                intent.installment, amount=amount, method=intent.method,
                reference=intent.ledger_reference,
            )
            ledger_row = "installment"
    elif intent.invoice_id:
        from products.cyed.fees.models import Payment

        if Payment.objects.filter(
            tenant_id=intent.tenant_id, invoice_id=intent.invoice_id,
            reference=intent.ledger_reference,
        ).exists():
            ledger_row = "already-present"
        else:
            Payment.objects.create(
                tenant_id=intent.tenant_id, invoice=intent.invoice, amount=amount,
                method=intent.method, paid_on=timezone.now().date(),
                reference=intent.ledger_reference,
            )
            intent.invoice.recalc_status()
            ledger_row = "invoice"
    else:
        # Nothing linked (e.g. a donation or a uniform-shop sale). The intent is
        # still a valid record of money received; there is simply no fee ledger
        # to credit, so it is marked reconciled to keep it out of the exception
        # report.
        ledger_row = "unlinked"

    intent.reconciled_at = timezone.now()
    intent.save(update_fields=["reconciled_at", "updated_at"])
    return ledger_row


def _reverse_on_ledger(intent: PaymentIntent, refund: Refund):
    """
    Back a refund out of the fee ledger as a negative payment row.

    Both ledgers derive status from the *sum* of their payment rows, so a
    negative row makes a fully-paid invoice correctly fall back to partial via
    the ledger's own recalc — no parallel refund bookkeeping to drift out of
    sync.
    """
    if intent.reconciled_at is None:
        return None
    reference = f"PIRF:{refund.id}"
    if intent.installment_id:
        from products.cyed.billing import services as billing_services
        from products.cyed.billing.models import InstallmentPayment

        if InstallmentPayment.objects.filter(
            tenant_id=intent.tenant_id, installment_id=intent.installment_id, reference=reference
        ).exists():
            return None
        billing_services.record_payment(
            intent.installment, amount=-q(refund.amount), method=intent.method, reference=reference,
        )
        return "installment"
    if intent.invoice_id:
        from products.cyed.fees.models import Payment

        if Payment.objects.filter(
            tenant_id=intent.tenant_id, invoice_id=intent.invoice_id, reference=reference
        ).exists():
            return None
        Payment.objects.create(
            tenant_id=intent.tenant_id, invoice=intent.invoice, amount=-q(refund.amount),
            method=intent.method, paid_on=timezone.now().date(), reference=reference,
        )
        intent.invoice.recalc_status()
        return "invoice"
    return None


def reconciliation_report(tenant_id, queryset=None) -> list[dict]:
    """
    Intents whose state disagrees with the ledger they point at.

    Every row here is money that either was taken and not credited, or was
    credited without a successful payment behind it. An empty report is the
    finance office's daily green light.
    """
    qs = queryset if queryset is not None else PaymentIntent.objects.filter(tenant_id=tenant_id)
    qs = qs.select_related("invoice", "installment", "installment__bill")
    rows: list[dict] = []

    from products.cyed.billing.models import InstallmentPayment
    from products.cyed.fees.models import Payment

    for intent in qs:
        discrepancy = ""
        linked_status = ""
        expected = q(intent.captured_amount)

        if intent.installment_id:
            inst = intent.installment
            linked_status = inst.status
            posted = InstallmentPayment.objects.filter(
                tenant_id=intent.tenant_id, installment_id=inst.id, reference=intent.ledger_reference
            ).exists()
        elif intent.invoice_id:
            inv = intent.invoice
            linked_status = inv.status
            posted = Payment.objects.filter(
                tenant_id=intent.tenant_id, invoice_id=inv.id, reference=intent.ledger_reference
            ).exists()
        else:
            linked_status = ""
            posted = False

        if intent.status == "succeeded":
            if not intent.linked_ref:
                discrepancy = "" if intent.reconciled_at else "unlinked_uncredited"
            elif not posted:
                discrepancy = "captured_not_posted"
            elif linked_status in ("unpaid", "draft", "issued", "overdue"):
                # Ledger row exists but the target still reads as unpaid — its
                # status was never recalculated, or another process reset it.
                discrepancy = "ledger_status_stale"
        elif intent.status in ("failed", "cancelled"):
            if posted:
                discrepancy = "posted_without_capture"
        elif intent.status == "refunded":
            if linked_status == "paid":
                discrepancy = "refunded_but_ledger_paid"
        elif intent.status in ("created", "pending") and posted:
            discrepancy = "posted_before_capture"

        if discrepancy:
            rows.append({
                "intent": str(intent.id),
                "status": intent.status,
                "provider": intent.provider,
                "provider_reference": intent.provider_reference,
                "amount": str(q(intent.amount)),
                "captured_amount": str(expected),
                "refunded_amount": str(q(intent.refunded_amount)),
                "linked": intent.linked_ref,
                "linked_status": linked_status,
                "ledger_row_present": posted,
                "reconciled_at": intent.reconciled_at.isoformat() if intent.reconciled_at else None,
                "discrepancy": discrepancy,
            })
    return rows


# ── webhooks ─────────────────────────────────────────────────────────────────
def _find_intent(data: dict, provider_name: str):
    """Locate the intent a webhook refers to, by any of the three handles."""
    intent_id = data.get("intent_id") or data.get("payment_intent")
    if intent_id:
        found = PaymentIntent.objects.filter(id=intent_id).first() if _looks_uuid(intent_id) else None
        if found:
            return found
    reference = data.get("provider_reference") or data.get("reference")
    if reference:
        found = PaymentIntent.objects.filter(
            provider=provider_name, provider_reference=reference
        ).first()
        if found:
            return found
    key = data.get("idempotency_key")
    if key:
        return PaymentIntent.objects.filter(idempotency_key=key).first()
    return None


def _looks_uuid(value) -> bool:
    import uuid as _uuid

    try:
        _uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def apply_webhook(raw_body: bytes, signature: str, provider_name: str | None = None):
    """
    Verify, record and apply one provider callback.

    Returns (WebhookEvent, http_status). Every call writes exactly one
    append-only WebhookEvent, including rejections — a forged callback is
    evidence, not noise. Order matters: the signature is checked against the
    raw bytes *before* the body is parsed or trusted for anything.
    """
    def _record(**kwargs) -> WebhookEvent:
        return WebhookEvent.objects.create(
            tenant_id=kwargs.pop("tenant_id", UNKNOWN_TENANT),
            provider=provider_name or "",
            payload=(raw_body or b"").decode("utf-8", errors="replace")[:100000],
            signature=(signature or "")[:255],
            **kwargs,
        )

    try:
        adapter = get_provider(provider_name)
    except ProviderNotConfigured as exc:
        return _record(verified=False, result="rejected_unconfigured", detail=str(exc)[:255]), 503

    try:
        verified = adapter.verify_webhook(raw_body or b"", signature or "")
    except ProviderNotConfigured as exc:
        # No shared secret → we cannot tell a real provider from an attacker.
        return _record(verified=False, result="rejected_unconfigured", detail=str(exc)[:255]), 503
    except PaymentProviderError as exc:
        return _record(verified=False, result="error", detail=str(exc)[:255]), 400

    if not verified:
        return _record(
            verified=False, result="rejected_signature",
            detail="HMAC-SHA256 signature did not match the raw request body.",
        ), 400

    try:
        payload = json.loads((raw_body or b"").decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
    except (ValueError, UnicodeDecodeError) as exc:
        return _record(verified=True, result="rejected_malformed", detail=str(exc)[:255]), 400

    event_id = str(payload.get("id") or "")[:255]
    event_type = str(payload.get("type") or "")[:100]
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    intent = _find_intent(data, adapter.name)
    tenant_id = intent.tenant_id if intent is not None else UNKNOWN_TENANT

    # Replay protection. A provider retrying a delivery it already got a 200 for
    # is normal traffic, not an error — record it and answer 200 without
    # touching the money a second time.
    if event_id and WebhookEvent.objects.filter(
        provider=adapter.name, event_id=event_id, processed=True, verified=True
    ).exists():
        return _record(
            tenant_id=tenant_id, event_id=event_id, event_type=event_type, intent=intent,
            verified=True, processed=False, result="duplicate",
            detail="Event already applied; ignored.",
        ), 200

    if intent is None:
        return _record(
            event_id=event_id, event_type=event_type, verified=True, result="unmatched",
            detail="No payment intent matches this event's references.",
        ), 200

    try:
        applied = _apply_event(intent, event_type, data)
    except (PaymentError, PaymentProviderError) as exc:
        return _record(
            tenant_id=tenant_id, event_id=event_id, event_type=event_type, intent=intent,
            verified=True, result="error", detail=str(exc)[:255],
        ), 400

    return _record(
        tenant_id=tenant_id, event_id=event_id, event_type=event_type, intent=intent,
        verified=True, processed=True, result="applied" if applied else "ignored",
        detail="" if applied else f"No handler for event type '{event_type}'.",
    ), 200


def _apply_event(intent: PaymentIntent, event_type: str, data: dict) -> bool:
    if event_type == EVT_SUCCEEDED:
        amount = q(data["amount"]) if data.get("amount") is not None else q(intent.amount)
        if amount > q(intent.amount):
            raise PaymentError(
                f"Webhook reports {amount} captured but the intent is only for {q(intent.amount)}."
            )
        if intent.status == "succeeded":
            return True  # already applied; idempotent no-op
        if intent.status in PaymentIntent.TERMINAL:
            raise PaymentError(f"Cannot mark a {intent.status} payment succeeded.")
        if data.get("provider_reference"):
            intent.provider_reference = str(data["provider_reference"])[:255]
        _settle(intent, amount)
        return True

    if event_type == EVT_FAILED:
        mark_failed(intent, str(data.get("failure_reason") or "provider_reported_failure"))
        return True

    if event_type == EVT_CANCELLED:
        if intent.status not in PaymentIntent.TERMINAL:
            cancel_intent(intent, str(data.get("reason") or "provider_cancelled"))
        return True

    if event_type == EVT_REFUNDED:
        amount = q(data["amount"]) if data.get("amount") is not None else None
        refund_intent(intent, amount=amount, reason=str(data.get("reason") or "provider_refund"),
                      actor="webhook")
        return True

    return False
