from rest_framework import serializers

from .models import Account, JournalEntry, JournalLine


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "tenant_id",
            "code",
            "name",
            "name_ar",
            "account_type",
            "parent_account",
            "is_active",
            "currency",
            "balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class JournalLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalLine
        fields = [
            "id",
            "tenant_id",
            "journal",
            "account",
            "debit",
            "credit",
            "description",
            "cost_center",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "tenant_id",
            "entry_date",
            "description",
            "reference",
            "status",
            "posted_by",
            "posted_at",
            "total_debit",
            "total_credit",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        instance = self.instance
        if instance is not None:
            lines = instance.lines.all()
            if lines.exists():
                total_debit = sum(line.debit for line in lines)
                total_credit = sum(line.credit for line in lines)
                if total_debit != total_credit:
                    raise serializers.ValidationError(
                        {"non_field_errors": "Total debit must equal total credit."}
                    )
        return attrs
