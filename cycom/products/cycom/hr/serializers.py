from rest_framework import serializers

from products.cycom.hr.models import Contract, Employee


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ContractSerializer(serializers.ModelSerializer):
    hourly_rate = serializers.DecimalField(max_digits=12, decimal_places=4, read_only=True)

    class Meta:
        model = Contract
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
