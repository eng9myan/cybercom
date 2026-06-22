import random
from rest_framework import serializers
from products.cymed.clinic.billing_bridge.models import ChargeCode, PriceList, ClinicService, ChargeItem

class ChargeCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeCode
        fields = "__all__"

class PriceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        fields = "__all__"

class ClinicServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicService
        fields = "__all__"

class ChargeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeItem
        fields = ["id", "encounter", "service", "quantity", "posted_to_erp", "erp_transaction_id"]
        read_only_fields = ["posted_to_erp", "erp_transaction_id"]

    def create(self, validated_data):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        validated_data["tenant_id"] = tenant_id

        # Mock ERP Post
        posted = True
        erp_tx_id = f"ERP-TX-{random.randint(10000, 99999)}"

        return ChargeItem.objects.create(
            posted_to_erp=posted,
            erp_transaction_id=erp_tx_id,
            **validated_data
        )
