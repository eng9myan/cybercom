from rest_framework import serializers

from products.cycom.expenses.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"
        read_only_fields = [
            "id",
            "tenant_id",
            "created_at",
            "updated_at",
            "status",
            "approved_by",
            "rejection_reason",
            "journal_entry",
        ]
