from rest_framework import serializers

from products.cycom.field_service.models import ServiceContract, ServiceTask


class ServiceContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceContract
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ServiceTaskSerializer(serializers.ModelSerializer):
    is_breached = serializers.BooleanField(read_only=True)
    contract_number = serializers.CharField(source="contract.contract_number", read_only=True, default="")

    class Meta:
        model = ServiceTask
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "completed_at", "sla_deadline",
        ]
