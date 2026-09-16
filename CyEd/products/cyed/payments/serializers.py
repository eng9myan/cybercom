from rest_framework import serializers

from core.serializers import ReadOnlyModelSerializer
from products.cyed.payments.models import PaymentIntent, Refund, WebhookEvent


class RefundSerializer(ReadOnlyModelSerializer):
    """
    Refunds are created through `POST /intents/{id}/refund/`, never by writing
    this model: the amount has to be validated against what was actually
    captured and the gateway has to be called. A writable serializer here would
    be a second, unguarded path to giving money away.
    """

    class Meta:
        model = Refund
        fields = "__all__"


class PaymentIntentSerializer(serializers.ModelSerializer):
    refunds = RefundSerializer(many=True, read_only=True)
    refundable_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_settled = serializers.BooleanField(read_only=True)
    linked_ref = serializers.CharField(read_only=True)

    class Meta:
        model = PaymentIntent
        fields = "__all__"
        # Everything the gateway owns is read-only. A client may say what it
        # wants to pay for; it may never assert that the money arrived.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "provider", "provider_reference", "captured_amount",
            "refunded_amount", "succeeded_at", "reconciled_at", "failure_reason",
            "created_by", "metadata",
        ]


class PaymentIntentCreateSerializer(serializers.Serializer):
    """
    Input for opening an intent. Separate from the model serializer because
    `idempotency_key` is required on the way in but is not something a caller
    should be able to PATCH afterwards.
    """

    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    idempotency_key = serializers.CharField(max_length=128)
    currency = serializers.CharField(max_length=3, required=False, default="AUD")
    method = serializers.ChoiceField(
        choices=[c[0] for c in PaymentIntent._meta.get_field("method").choices],
        required=False, default="card",
    )
    provider = serializers.CharField(max_length=50, required=False, allow_blank=True)
    invoice = serializers.UUIDField(required=False, allow_null=True)
    installment = serializers.UUIDField(required=False, allow_null=True)
    payer_email = serializers.EmailField(required=False, allow_blank=True)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)

    def validate(self, attrs):
        if attrs.get("invoice") and attrs.get("installment"):
            raise serializers.ValidationError(
                "An intent may target an invoice or an installment, not both."
            )
        return attrs


class WebhookEventSerializer(ReadOnlyModelSerializer):
    """Append-only audit record — readable by security, writable by nobody."""

    class Meta:
        model = WebhookEvent
        fields = "__all__"
