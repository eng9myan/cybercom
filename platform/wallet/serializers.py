from decimal import Decimal

from rest_framework import serializers

from platform.wallet.models import WalletLedgerEntry


class WalletTopUpSerializer(serializers.Serializer):
    person_id = serializers.UUIDField(required=False)
    currency = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class WalletDebitSerializer(serializers.Serializer):
    person_id = serializers.UUIDField(required=False)
    currency = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class WalletLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletLedgerEntry
        fields = ["id", "entry_type", "amount", "balance_after", "reference", "created_by", "created_at"]
