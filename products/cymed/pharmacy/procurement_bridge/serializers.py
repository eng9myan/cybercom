from rest_framework import serializers
from .models import ProcurementRequest


class ProcurementRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcurementRequest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "request_number"]
