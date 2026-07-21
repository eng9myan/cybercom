from rest_framework import serializers

from platform.wallet.models import CheckoutReceipt, CheckoutReceiptLine


class CymedOrderPaymentItemSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class CyshopCartItemSerializer(serializers.Serializer):
    cyshop_tenant_id = serializers.UUIDField()
    company_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    item_name = serializers.CharField(max_length=255)
    qty = serializers.DecimalField(max_digits=12, decimal_places=4)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=4)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class CheckoutRequestSerializer(serializers.Serializer):
    currency = serializers.CharField(max_length=3)
    cymed_items = CymedOrderPaymentItemSerializer(many=True, required=False, default=list)
    cyshop_items = CyshopCartItemSerializer(many=True, required=False, default=list)
    cyid_token = serializers.CharField(required=False, allow_blank=True, default="")
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")
    person_id = serializers.UUIDField(required=False)


class CheckoutReceiptLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutReceiptLine
        fields = ["id", "item_type", "external_reference", "description", "amount"]


class CheckoutReceiptSerializer(serializers.ModelSerializer):
    lines = CheckoutReceiptLineSerializer(many=True, read_only=True)

    class Meta:
        model = CheckoutReceipt
        fields = ["id", "currency", "total_amount", "lines", "created_at"]
