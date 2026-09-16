from rest_framework import serializers

from products.cyed.payroll.models import PayrollRun, Payslip, PayslipLine, SalaryComponent


class PayslipLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayslipLine
        fields = ["id", "kind", "description", "amount"]
        read_only_fields = fields


class PayslipSerializer(serializers.ModelSerializer):
    lines = PayslipLineSerializer(many=True, read_only=True)
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = Payslip
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "gross", "paye_tax", "superannuation", "net",
            "hours_worked", "unpaid_days", "unpaid_deduction", "leave_days",
            "allowances_total", "deductions_total", "created_at", "updated_at",
        ]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}" if obj.staff_id else ""


class PayrollRunSerializer(serializers.ModelSerializer):
    payslips = PayslipSerializer(many=True, read_only=True)

    class Meta:
        model = PayrollRun
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("period_start") or getattr(self.instance, "period_start", None)
        end = attrs.get("period_end") or getattr(self.instance, "period_end", None)
        if start and end and end < start:
            raise serializers.ValidationError({"period_end": "Period end cannot be before period start."})
        return attrs


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
