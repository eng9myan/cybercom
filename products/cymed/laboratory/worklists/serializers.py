from rest_framework import serializers
from .models import Analyzer, AnalyzerInterface, AnalyzerMessage, AnalyzerResult, LabWorklist, WorklistItem, WorklistQueue, TechnologistAssignment

class AnalyzerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analyzer
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class AnalyzerInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyzerInterface
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class AnalyzerMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyzerMessage
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class AnalyzerResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyzerResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class WorklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorklistItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class LabWorklistSerializer(serializers.ModelSerializer):
    items = WorklistItemSerializer(many=True, read_only=True)
    class Meta:
        model = LabWorklist
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class TechnologistAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnologistAssignment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
