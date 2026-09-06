from rest_framework import serializers

from .models import (
    BankAccount, BankStatement, BankStatementLine, ReconciliationSession,
)


class BankAccountSerializer(serializers.ModelSerializer):
    book_balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = BankAccount
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def create(self, v):
        v["tenant_id"] = self.context["request"].tenant_id
        return super().create(v)


class BankStatementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementLine
        fields = ["id", "bank_account", "statement", "txn_date", "description",
                  "reference", "amount", "matched", "match_type", "match_id",
                  "match_note", "reconciled"]
        read_only_fields = ["id", "tenant_id", "bank_account", "statement"]


class BankStatementSerializer(serializers.ModelSerializer):
    lines = BankStatementLineSerializer(many=True, read_only=True)

    class Meta:
        model = BankStatement
        fields = ["id", "bank_account", "reference", "statement_date",
                  "opening_balance", "closing_balance", "line_count", "lines", "created_at"]
        read_only_fields = fields


class ReconciliationSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationSession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "book_balance", "difference",
                            "status", "completed_at", "created_at", "updated_at"]

    def create(self, v):
        v["tenant_id"] = self.context["request"].tenant_id
        return super().create(v)
