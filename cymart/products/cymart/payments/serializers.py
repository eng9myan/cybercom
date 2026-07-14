from rest_framework import serializers

from .models import Dispute, PaymentIntent


class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = [
            "id", "order_id", "tenant_id", "provider", "provider_reference",
            "currency", "amount", "captured_amount", "refunded_amount",
            "status", "failure_reason", "created_at", "updated_at",
        ]
        read_only_fields = fields


class DisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = [
            "id", "order_id", "payment_intent", "raised_by_customer_id",
            "reason", "status", "resolution_notes", "resolved_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "resolution_notes", "resolved_at", "created_at", "updated_at"]
