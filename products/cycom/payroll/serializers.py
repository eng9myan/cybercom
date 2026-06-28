from rest_framework import serializers
from .models import PayrollRun, Payslip


class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = [
            "id",
            "payroll_run",
            "employee_id",
            "basic_salary",
            "allowances",
            "deductions",
            "net_salary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "net_salary", "created_at", "updated_at"]


class PayrollRunSerializer(serializers.ModelSerializer):
    payslips = PayslipSerializer(many=True, read_only=True)

    class Meta:
        model = PayrollRun
        fields = [
            "id",
            "run_date",
            "status",
            "total_gross",
            "total_deductions",
            "total_net",
            "processed_by",
            "payslips",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
