"""
Payment layer for CyEd.

The audit found the system "cannot take money": a payment was a free-text
`method` label on a fees.Payment row with nothing behind it. This app adds the
missing machinery — a PaymentIntent state machine, a provider-agnostic gateway
seam (see providers.py), signed asynchronous webhooks, refunds, and
reconciliation back onto the existing fees.Invoice / billing.Installment
ledgers.

CARD DATA IS NEVER STORED HERE. There is deliberately no PAN, expiry, CVV,
cardholder-name or track-data field on any model in this module, and none may
be added: CyEd stays out of PCI-DSS scope by never letting card data touch the
server. A real provider (Stripe / eWAY / Pin Payments) tokenises the card in the
browser and hands us an opaque token; only that token's *result* — a provider
reference string — is persisted, in `provider_reference`.
"""

import uuid
from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel

# Webhooks can arrive before we know which tenant they belong to (bad signature,
# unknown reference, malformed body). BaseModel.tenant_id is NOT NULL, but those
# events are exactly the ones a security review wants to read, so they are
# recorded against this sentinel rather than dropped on the floor.
UNKNOWN_TENANT = uuid.UUID(int=0)

# Mirrors the method vocabulary already used by cyed_fees.Payment and
# cyed_billing.InstallmentPayment so reconciliation writes a value those ledgers
# already understand.
METHOD_CHOICES = [
    ("card", "Card"),
    ("bank_transfer", "Bank Transfer"),
    ("bpay", "BPAY"),
    ("direct_debit", "Direct Debit"),
    ("cash", "Cash"),
]


class PaymentIntent(BaseModel):
    """
    One attempt to collect a specific amount of money.

    The lifecycle is: created → pending (provider has authorised / is awaiting
    funds) → succeeded | failed | cancelled. A refund does not create a new
    state until the whole captured amount is returned, at which point the intent
    becomes `refunded`; a partial refund leaves the intent `succeeded` with
    `refunded_amount` > 0, because the money genuinely did change hands.
    """

    STATUS_CHOICES = [
        ("created", "Created"),
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("cancelled", "Cancelled"),
    ]
    # Terminal states never transition again.
    TERMINAL = {"succeeded", "failed", "refunded", "cancelled"}

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="AUD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="card")

    provider = models.CharField(max_length=50)
    # Opaque handle issued by the provider (Stripe `pi_...`, eWAY transaction
    # id, or a MANUAL-xxxx receipt for an offline payment). Never card data.
    provider_reference = models.CharField(max_length=255, blank=True)

    # Client-supplied de-duplication token. Unique per tenant: re-posting the
    # same key returns the original intent instead of charging a parent twice.
    idempotency_key = models.CharField(max_length=128)

    invoice = models.ForeignKey(
        "cyed_fees.Invoice", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payment_intents",
    )
    installment = models.ForeignKey(
        "cyed_billing.Installment", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payment_intents",
    )

    payer_email = models.EmailField(blank=True)
    description = models.CharField(max_length=255, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    captured_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    created_by = models.CharField(max_length=255, blank=True)
    succeeded_at = models.DateTimeField(null=True, blank=True)
    # Set once the money has been written onto the linked invoice/installment
    # ledger. Guards against double-applying a replayed webhook.
    reconciled_at = models.DateTimeField(null=True, blank=True)
    # Non-sensitive provider echo (last4 is NOT stored; this is for ids//labels).
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cyed_payment_intents"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "idempotency_key"], name="uniq_payment_intent_idempotency"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="payment_intent_amount_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(refunded_amount__lte=models.F("captured_amount")),
                name="payment_intent_refund_within_capture",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "status"], name="idx_pay_intent_tenant_status"),
            models.Index(fields=["provider", "provider_reference"], name="idx_pay_intent_provider_ref"),
        ]

    # ── derived ──────────────────────────────────────────────────────────────
    @property
    def refundable_amount(self) -> Decimal:
        return Decimal(self.captured_amount) - Decimal(self.refunded_amount)

    @property
    def is_settled(self) -> bool:
        return self.status in ("succeeded", "refunded")

    @property
    def linked_ref(self) -> str:
        if self.installment_id:
            return f"cyed_billing.Installment:{self.installment_id}"
        if self.invoice_id:
            return f"cyed_fees.Invoice:{self.invoice_id}"
        return ""

    @property
    def ledger_reference(self) -> str:
        """Reference written onto the fees/billing payment row it produces."""
        return f"PI:{self.id}"

    def __str__(self):
        return f"PaymentIntent {self.amount} {self.currency} ({self.status}/{self.provider})"


class Refund(BaseModel):
    """A full or partial return of a captured PaymentIntent."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]

    intent = models.ForeignKey(PaymentIntent, on_delete=models.CASCADE, related_name="refunds")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reason = models.CharField(max_length=255, blank=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_payment_refunds"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="refund_amount_positive"),
        ]

    def __str__(self):
        return f"Refund {self.amount} on {self.intent_id} ({self.status})"


class WebhookEvent(BaseModel):
    """
    Append-only log of every provider callback we received, verified or not.

    Deliberately NOT uniquely constrained on (provider, event_id): a replayed or
    forged event must still be recorded, and a DB constraint would turn the
    second delivery into an IntegrityError instead of an audit row. Replay
    protection is enforced in services.apply_webhook by looking for an existing
    *applied* event with the same id.
    """

    RESULTS = [
        ("applied", "Applied"),
        ("duplicate", "Duplicate — ignored"),
        ("rejected_signature", "Rejected — bad signature"),
        ("rejected_unconfigured", "Rejected — no webhook secret configured"),
        ("rejected_malformed", "Rejected — malformed payload"),
        ("unmatched", "No matching payment intent"),
        ("ignored", "Understood but not actionable"),
        ("error", "Error while applying"),
    ]

    provider = models.CharField(max_length=50)
    event_id = models.CharField(max_length=255, blank=True)
    event_type = models.CharField(max_length=100, blank=True)
    # Raw request body exactly as received — this is what the signature covers,
    # so it is what an investigator has to be able to re-hash.
    payload = models.TextField(blank=True)
    signature = models.CharField(max_length=255, blank=True)
    verified = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    result = models.CharField(max_length=30, choices=RESULTS, default="error")
    detail = models.CharField(max_length=255, blank=True)
    intent = models.ForeignKey(
        PaymentIntent, on_delete=models.SET_NULL, null=True, blank=True, related_name="webhook_events"
    )

    class Meta:
        db_table = "cyed_payment_webhook_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider", "event_id"], name="idx_pay_webhook_provider_event"),
            models.Index(fields=["tenant_id", "created_at"], name="idx_pay_webhook_tenant_time"),
        ]

    def __str__(self):
        return f"Webhook {self.provider}/{self.event_type} {self.event_id} ({self.result})"
