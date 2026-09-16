from rest_framework import serializers

from products.cyed.finance.models import (
    Account, BankStatement, BankStatementLine, Budget, BudgetLine, JournalEntry, JournalLine,
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
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)
    is_balanced = serializers.ReadOnlyField()

    class Meta:
        model = JournalEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "posted", "created_at", "updated_at"]


class BudgetLineSerializer(serializers.ModelSerializer):
    account_code = serializers.SerializerMethodField()
    actual_amount = serializers.SerializerMethodField()
    variance_amount = serializers.SerializerMethodField()

    class Meta:
        model = BudgetLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_account_code(self, obj):
        return obj.account.code if obj.account_id else ""

    def get_actual_amount(self, obj):
        return str(obj.actual())

    def get_variance_amount(self, obj):
        return str(obj.variance())


class BudgetSerializer(serializers.ModelSerializer):
    lines = BudgetLineSerializer(many=True, read_only=True)

    class Meta:
        model = Budget
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        # (tenant_id, fiscal_year, name) is unique; tenant is injected on save.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        year = attrs.get("fiscal_year") or getattr(self.instance, "fiscal_year", None)
        name = attrs.get("name") or getattr(self.instance, "name", None)
        qs = Budget.objects.filter(tenant_id=tenant_id, fiscal_year=year, name=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A budget with this name already exists for that fiscal year.")
        return attrs


class BankStatementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementLine
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "is_reconciled", "matched_entry", "reconciled_at", "reconciled_by",
        ]


class BankStatementSerializer(serializers.ModelSerializer):
    lines = BankStatementLineSerializer(many=True, read_only=True)
    account_code = serializers.SerializerMethodField()
    expected_closing = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    balances = serializers.BooleanField(read_only=True)
    unreconciled_count = serializers.IntegerField(read_only=True)
    is_fully_reconciled = serializers.BooleanField(read_only=True)

    class Meta:
        model = BankStatement
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "imported_by", "reconciled_at", "source_filename",
        ]

    def get_account_code(self, obj):
        return f"{obj.account.code} {obj.account.name}" if obj.account_id else ""

    def validate(self, attrs):
        start = attrs.get("period_start") or getattr(self.instance, "period_start", None)
        end = attrs.get("period_end") or getattr(self.instance, "period_end", None)
        if start and end and end < start:
            raise serializers.ValidationError({"period_end": "Period end cannot be before period start."})
        account = attrs.get("account") or getattr(self.instance, "account", None)
        # Reconciling a revenue or expense account is a category error — a bank
        # statement can only belong to a cash/bank asset account.
        if account is not None and account.account_type != "asset":
            raise serializers.ValidationError(
                {"account": "A bank statement must be attached to an asset (cash/bank) account."}
            )
        return attrs
