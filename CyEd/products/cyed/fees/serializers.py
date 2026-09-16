from rest_framework import serializers

from products.cyed.fees.models import FeeSchedule, Invoice, Payment


class FeeScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeSchedule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    # DecimalField (not ReadOnlyField) so these serialize as strings, matching
    # how DRF renders `amount` — consistent JSON number typing for clients.
    paid_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
