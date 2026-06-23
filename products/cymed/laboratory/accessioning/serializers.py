from rest_framework import serializers
from .models import Accession, AccessionBatch, AccessionBatchItem, AccessionAudit, AccessionNumberSequence

class AccessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "accession_number", "accessioned_at"]

class AccessionBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessionBatch
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class AccessionBatchItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessionBatchItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class AccessionAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessionAudit
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
