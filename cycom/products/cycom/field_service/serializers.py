from rest_framework import serializers

from products.cycom.field_service.models import ServiceTask


class ServiceTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceTask
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "completed_at",
        ]
