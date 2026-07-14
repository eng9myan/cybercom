import uuid
from decimal import Decimal

import pytest

from products.cymart.payments.models import DisputeStatus, PaymentIntentStatus
from products.cymart.payments.services import DisputeService, PaymentError, PaymentService


@pytest.mark.django_db
class TestPaymentService:
    """Master spec section 17: authorize/capture/void/refund/partial
    refund, never storing raw card details (only a provider token)."""

    def test_authorize_success(self):
        intent = PaymentService().authorize(
            order_id=uuid.uuid4(), tenant_id=uuid.uuid4(),
            amount=Decimal("100.00"), currency="USD", payment_method_token="tok_visa",
        )
        assert intent.status == PaymentIntentStatus.AUTHORIZED
        assert intent.provider_reference != ""
        # Never stores anything that looks like a raw card number — only
        # the opaque token the caller supplied.
        assert intent.payment_method_token == "tok_visa"

    def test_authorize_decline(self):
        intent = PaymentService().authorize(
            order_id=uuid.uuid4(), tenant_id=uuid.uuid4(),
            amount=Decimal("100.00"), currency="USD", payment_method_token="decline_insufficient_funds",
        )
        assert intent.status == PaymentIntentStatus.FAILED
        assert intent.failure_reason != ""

    def test_capture_full_amount(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent)
        assert intent.status == PaymentIntentStatus.CAPTURED
        assert intent.captured_amount == Decimal("100.00")

    def test_capture_partial_amount(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent, amount=Decimal("60.00"))
        assert intent.captured_amount == Decimal("60.00")

    def test_cannot_capture_unauthorized_intent(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "decline_x")
        with pytest.raises(PaymentError):
            svc.capture(intent)

    def test_cannot_capture_twice(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent)
        with pytest.raises(PaymentError):
            svc.capture(intent)

    def test_void_releases_authorization(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.void(intent)
        assert intent.status == PaymentIntentStatus.VOIDED

    def test_cannot_void_captured_intent(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent)
        with pytest.raises(PaymentError):
            svc.void(intent)

    def test_full_refund(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent)
        intent = svc.refund(intent)
        assert intent.status == PaymentIntentStatus.REFUNDED
        assert intent.refunded_amount == Decimal("100.00")

    def test_partial_refund(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent)
        intent = svc.refund(intent, amount=Decimal("30.00"))
        assert intent.status == PaymentIntentStatus.PARTIALLY_REFUNDED
        assert intent.refunded_amount == Decimal("30.00")

    def test_sequential_partial_refunds_up_to_full(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent)
        intent = svc.refund(intent, amount=Decimal("40.00"))
        assert intent.status == PaymentIntentStatus.PARTIALLY_REFUNDED
        intent = svc.refund(intent, amount=Decimal("60.00"))
        assert intent.status == PaymentIntentStatus.REFUNDED
        assert intent.refunded_amount == Decimal("100.00")

    def test_cannot_refund_more_than_captured(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = svc.capture(intent)
        with pytest.raises(PaymentError):
            svc.refund(intent, amount=Decimal("150.00"))

    def test_cannot_refund_uncaptured_intent(self):
        svc = PaymentService()
        intent = svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        with pytest.raises(PaymentError):
            svc.refund(intent)


@pytest.mark.django_db
class TestDisputeService:
    def test_open_and_resolve_for_merchant(self):
        pay_svc = PaymentService()
        intent = pay_svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = pay_svc.capture(intent)

        dispute = DisputeService().open_dispute(
            order_id=uuid.uuid4(), payment_intent=intent, customer_id=uuid.uuid4(),
            reason="Item not as described",
        )
        assert dispute.status == DisputeStatus.OPEN

        dispute = DisputeService().resolve(dispute, in_favor_of="merchant", notes="Evidence supports merchant.")
        assert dispute.status == DisputeStatus.RESOLVED_MERCHANT
        assert dispute.resolved_at is not None

    def test_resolve_for_customer(self):
        pay_svc = PaymentService()
        intent = pay_svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = pay_svc.capture(intent)
        dispute = DisputeService().open_dispute(uuid.uuid4(), intent, uuid.uuid4(), "Never arrived")
        dispute = DisputeService().resolve(dispute, in_favor_of="customer")
        assert dispute.status == DisputeStatus.RESOLVED_CUSTOMER

    def test_resolve_requires_valid_party(self):
        pay_svc = PaymentService()
        intent = pay_svc.authorize(uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), "USD", "tok_visa")
        intent = pay_svc.capture(intent)
        dispute = DisputeService().open_dispute(uuid.uuid4(), intent, uuid.uuid4(), "reason")
        with pytest.raises(ValueError):
            DisputeService().resolve(dispute, in_favor_of="nobody")
