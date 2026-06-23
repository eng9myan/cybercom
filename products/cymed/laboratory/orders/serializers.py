from rest_framework import serializers
from .models import LabTest, LabPanel, LabOrder, LabOrderItem, LabOrderDiagnosis, LabOrderAttachment, LabOrderStatusHistory

class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class LabPanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabPanel
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class LabOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOrderItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class LabOrderSerializer(serializers.ModelSerializer):
    items = LabOrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = LabOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "order_number"]

class LabOrderDiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOrderDiagnosis
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class LabOrderAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOrderAttachment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class LabOrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOrderStatusHistory
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
