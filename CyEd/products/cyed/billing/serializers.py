from rest_framework import serializers

from products.cyed.billing.models import (
    BillLineItem,
    CreditNote,
    DunningAction,
    DunningCase,
    FeePlan,
    Installment,
    InstallmentPayment,
    SiblingDiscountRule,
    StudentBill,
)


class FeePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeePlan
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CreditNoteSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = CreditNote
        fields = "__all__"
        # Issue and cancel are actions, not field edits: an issued note is a
        # document, and letting `status` be PATCHed would let one be un-issued
        # without applying or reversing anything.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at", "number", "status",
            "issued_on", "issued_by", "cancelled_on", "cancelled_by", "cancel_reason",
            "journal_reference",
        ]

    def validate(self, attrs):
        bill = attrs.get("bill", getattr(self.instance, "bill", None))
        installment = attrs.get("installment", getattr(self.instance, "installment", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        if installment is not None and bill is not None and installment.bill_id != bill.id:
            raise serializers.ValidationError(
                {"installment": "That installment belongs to a different bill."}
            )
        target_bill = bill or (installment.bill if installment else None)
        if target_bill is not None and student is not None and target_bill.student_id != student.id:
            raise serializers.ValidationError(
                {"student": "The credit note names a different student from the bill it credits."}
            )
        return attrs


class DunningActionSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)

    class Meta:
        model = DunningAction
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DunningCaseSerializer(serializers.ModelSerializer):
    actions = DunningActionSerializer(many=True, read_only=True)
    family_name = serializers.CharField(source="family.name", read_only=True)
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    current_overdue = serializers.SerializerMethodField()

    class Meta:
        model = DunningCase
        fields = "__all__"
        # The ladder is climbed through actions so its ordering and waiting
        # rules cannot be bypassed by PATCHing `stage`.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at", "stage", "status",
            "opened_on", "opening_balance", "last_action_on", "paused_until",
            "pause_reason", "resolved_on", "resolution_note",
        ]

    def get_current_overdue(self, obj) -> str:
        from products.cyed.billing.collections import family_overdue

        return str(family_overdue(obj.family))


class SiblingDiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiblingDiscountRule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate_categories(self, value):
        """
        Guard the one mistake that quietly costs money: a typo'd category name
        matches no line item, so the discount silently computes to zero and
        nobody notices until a parent complains.
        """
        if not value:
            return value
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise serializers.ValidationError("categories must be a list of strings.")
        valid = {c[0] for c in BillLineItem.CATEGORIES}
        unknown = sorted(set(value) - valid)
        if unknown:
            raise serializers.ValidationError(
                f"Unknown line-item categories: {', '.join(unknown)}. Valid: {', '.join(sorted(valid))}."
            )
        return value


class BillLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLineItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class InstallmentPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPayment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class InstallmentSerializer(serializers.ModelSerializer):
    paid_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payments = InstallmentPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Installment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "created_at", "updated_at"]


class StudentBillSerializer(serializers.ModelSerializer):
    line_items = BillLineItemSerializer(many=True, read_only=True)
    installments = InstallmentSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = StudentBill
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
