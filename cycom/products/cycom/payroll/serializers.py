from django.db import transaction
from rest_framework import serializers

from products.cycom.accounting.sequencing import (
    allocate_document_number,
    can_override_document_number,
)
from products.cycom.payroll.models import AttendanceRecord, PayrollRun, Payslip


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "late_minutes", "overtime_minutes", "created_at", "updated_at"]


class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "base_salary", "allowances_total", "overtime_amount",
            "late_deduction", "gross_pay", "net_pay", "status", "created_at", "updated_at",
        ]


class PayrollRunSerializer(serializers.ModelSerializer):
    payslips = PayslipSerializer(many=True, read_only=True)
    # A-4: auto-allocated from a per-tenant/year gapless sequence when omitted.
    number = serializers.CharField(required=False, allow_blank=True, max_length=100)

    class Meta:
        model = PayrollRun
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "journal_entry", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        if attrs.get("number") and request is not None and not can_override_document_number(request):
            raise serializers.ValidationError(
                {"number": "You are not allowed to set the run number manually; "
                           "leave it blank to have it auto-generated."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        if not validated_data.get("number"):
            validated_data["number"] = allocate_document_number(
                validated_data["tenant_id"], "payroll_run",
                when=validated_data.get("period_start"),
            )
        return super().create(validated_data)
