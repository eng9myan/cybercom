from rest_framework import serializers

from products.cycom.accounting.models import Account, JournalEntry, JournalLine


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class JournalLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "entry", "created_at", "updated_at"]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True)

    class Meta:
        model = JournalEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        lines = attrs.get("lines", [])
        total_debit = sum(line.get("debit", 0) for line in lines)
        total_credit = sum(line.get("credit", 0) for line in lines)
        if lines and total_debit != total_credit:
            raise serializers.ValidationError(
                f"Journal entry is not balanced: debit {total_debit} != credit {total_credit}."
            )
        return attrs

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        entry = JournalEntry.objects.create(**validated_data)
        for line_data in lines_data:
            JournalLine.objects.create(
                entry=entry, tenant_id=validated_data["tenant_id"], **line_data
            )
        return entry
