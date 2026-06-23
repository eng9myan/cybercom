from rest_framework import serializers
from .models import ReferenceLab, ReferenceLabRouting, ReferenceLabOrder, ReferenceLabResult

class ReferenceLabSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceLab
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class ReferenceLabRoutingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceLabRouting
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class ReferenceLabOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceLabOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class ReferenceLabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceLabResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
