from rest_framework import serializers

from products.cycom.accounting.models import (
    Account,
    BankStatementLine,
    Budget,
    BudgetLine,
    DepreciationEntry,
    FixedAsset,
    JournalEntry,
    JournalLine,
)


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


class BankStatementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "matched_line", "is_reconciled",
                             "reconciled_at", "created_at", "updated_at"]


class DepreciationEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DepreciationEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "asset", "journal_entry", "created_at", "updated_at"]


class FixedAssetSerializer(serializers.ModelSerializer):
    depreciation_entries = DepreciationEntrySerializer(many=True, read_only=True)
    monthly_depreciation = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    accumulated_depreciation = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    net_book_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = FixedAsset
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "disposed_at", "created_at", "updated_at"]


class BudgetLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "budget", "created_at", "updated_at"]


class BudgetSerializer(serializers.ModelSerializer):
    lines = BudgetLineSerializer(many=True, required=False)

    class Meta:
        model = Budget
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", [])
        budget = Budget.objects.create(**validated_data)
        for line_data in lines_data:
            BudgetLine.objects.create(budget=budget, tenant_id=validated_data["tenant_id"], **line_data)
        budget.refresh_from_db()
        return budget
