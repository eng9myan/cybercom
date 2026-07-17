from rest_framework import serializers

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

    class Meta:
        model = PayrollRun
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "journal_entry", "created_at", "updated_at"]
