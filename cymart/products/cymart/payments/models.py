import uuid

from django.db import models


class PaymentIntentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    CAPTURED = "captured", "Captured"
    VOIDED = "voided", "Voided"
    REFUNDED = "refunded", "Refunded"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    FAILED = "failed", "Failed"


class PaymentIntent(models.Model):
    """
    Master spec section 17: payment-provider abstraction, authorize/
    capture/void/refund/partial-refund. Never stores raw card details —
    only a provider-issued token/reference, same as every real gateway
    requires (PCI scope stays with the provider, not here).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(db_index=True)

    provider = models.CharField(max_length=32, default="sandbox")
    provider_reference = models.CharField(max_length=128, blank=True)
    payment_method_token = models.CharField(
        max_length=128, help_text="Opaque token from the provider's client SDK — never a raw card number."
    )

    currency = models.CharField(max_length=3, default="USD")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    captured_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(
        max_length=24, choices=PaymentIntentStatus.choices, default=PaymentIntentStatus.PENDING
    )
    failure_reason = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_payment_intent"
        indexes = [models.Index(fields=["order_id"]), models.Index(fields=["tenant_id", "status"])]

    def __str__(self):
        return f"PaymentIntent({self.id}, {self.status}, {self.amount} {self.currency})"


class DisputeStatus(models.TextChoices):
    OPEN = "open", "Open"
    UNDER_REVIEW = "under_review", "Under Review"
    RESOLVED_MERCHANT = "resolved_merchant", "Resolved — Merchant"
    RESOLVED_CUSTOMER = "resolved_customer", "Resolved — Customer"
    CLOSED = "closed", "Closed"


class Dispute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(db_index=True)
    payment_intent = models.ForeignKey(
        PaymentIntent, on_delete=models.PROTECT, related_name="disputes"
    )
    raised_by_customer_id = models.UUIDField()
    reason = models.CharField(max_length=300)
    status = models.CharField(max_length=24, choices=DisputeStatus.choices, default=DisputeStatus.OPEN)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_dispute"

    def __str__(self):
        return f"Dispute({self.id}, {self.status})"
