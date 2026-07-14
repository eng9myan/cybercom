import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string

from .models import Dispute, DisputeStatus, PaymentIntent, PaymentIntentStatus
from .providers import SandboxPaymentProvider


class PaymentError(Exception):
    pass


def get_provider():
    """Provider is swappable via settings.CYMART_PAYMENT_PROVIDER (a dotted
    class path) — defaults to the sandbox since no real gateway credentials
    exist in this environment. A real deployment sets this to a real
    adapter implementing the same PaymentProvider interface."""
    provider_path = getattr(settings, "CYMART_PAYMENT_PROVIDER", None)
    if provider_path:
        return import_string(provider_path)()
    return SandboxPaymentProvider()


class PaymentService:
    def __init__(self, provider=None):
        self.provider = provider or get_provider()

    def authorize(
        self,
        order_id: uuid.UUID,
        tenant_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        payment_method_token: str,
    ) -> PaymentIntent:
        intent = PaymentIntent.objects.create(
            order_id=order_id,
            tenant_id=tenant_id,
            amount=amount,
            currency=currency,
            payment_method_token=payment_method_token,
        )
        result = self.provider.authorize(amount, currency, payment_method_token)
        if result.success:
            intent.status = PaymentIntentStatus.AUTHORIZED
            intent.provider_reference = result.provider_reference
        else:
            intent.status = PaymentIntentStatus.FAILED
            intent.failure_reason = result.failure_reason
        intent.save(update_fields=["status", "provider_reference", "failure_reason", "updated_at"])
        return intent

    def capture(self, intent: PaymentIntent, amount: "Decimal | None" = None) -> PaymentIntent:
        if intent.status != PaymentIntentStatus.AUTHORIZED:
            raise PaymentError(
                f"Cannot capture PaymentIntent {intent.id}: status is '{intent.status}', not 'authorized'."
            )
        capture_amount = amount if amount is not None else intent.amount
        result = self.provider.capture(intent.provider_reference, capture_amount)
        if not result.success:
            raise PaymentError(f"Capture failed: {result.failure_reason}")
        intent.status = PaymentIntentStatus.CAPTURED
        intent.captured_amount = capture_amount
        intent.save(update_fields=["status", "captured_amount", "updated_at"])
        return intent

    def void(self, intent: PaymentIntent) -> PaymentIntent:
        if intent.status != PaymentIntentStatus.AUTHORIZED:
            raise PaymentError(
                f"Cannot void PaymentIntent {intent.id}: status is '{intent.status}', not 'authorized'."
            )
        result = self.provider.void(intent.provider_reference)
        if not result.success:
            raise PaymentError(f"Void failed: {result.failure_reason}")
        intent.status = PaymentIntentStatus.VOIDED
        intent.save(update_fields=["status", "updated_at"])
        return intent

    def refund(self, intent: PaymentIntent, amount: "Decimal | None" = None) -> PaymentIntent:
        if intent.status not in (PaymentIntentStatus.CAPTURED, PaymentIntentStatus.PARTIALLY_REFUNDED):
            raise PaymentError(
                f"Cannot refund PaymentIntent {intent.id}: status is '{intent.status}', "
                "must be 'captured' or 'partially_refunded'."
            )
        refund_amount = amount if amount is not None else (intent.captured_amount - intent.refunded_amount)
        if refund_amount <= 0:
            raise PaymentError("Refund amount must be positive.")
        if intent.refunded_amount + refund_amount > intent.captured_amount:
            raise PaymentError("Refund amount exceeds captured amount remaining.")

        result = self.provider.refund(intent.provider_reference, refund_amount)
        if not result.success:
            raise PaymentError(f"Refund failed: {result.failure_reason}")

        with transaction.atomic():
            intent.refunded_amount += refund_amount
            intent.status = (
                PaymentIntentStatus.REFUNDED
                if intent.refunded_amount >= intent.captured_amount
                else PaymentIntentStatus.PARTIALLY_REFUNDED
            )
            intent.save(update_fields=["refunded_amount", "status", "updated_at"])
        return intent


class DisputeService:
    def open_dispute(
        self, order_id: uuid.UUID, payment_intent: PaymentIntent, customer_id: uuid.UUID, reason: str
    ) -> Dispute:
        return Dispute.objects.create(
            order_id=order_id,
            payment_intent=payment_intent,
            raised_by_customer_id=customer_id,
            reason=reason,
        )

    def resolve(self, dispute: Dispute, in_favor_of: str, notes: str = "") -> Dispute:
        if in_favor_of not in ("merchant", "customer"):
            raise ValueError("in_favor_of must be 'merchant' or 'customer'.")
        from django.utils import timezone

        dispute.status = (
            DisputeStatus.RESOLVED_MERCHANT if in_favor_of == "merchant" else DisputeStatus.RESOLVED_CUSTOMER
        )
        dispute.resolution_notes = notes
        dispute.resolved_at = timezone.now()
        dispute.save(update_fields=["status", "resolution_notes", "resolved_at", "updated_at"])
        return dispute
