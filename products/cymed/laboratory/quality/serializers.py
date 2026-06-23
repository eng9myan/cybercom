from rest_framework import serializers
from .models import QualityRule, QualityControl, QualityRun, QualityFailure, ProficiencyTest

class QualityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityRule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class QualityControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityControl
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class QualityRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityRun
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "z_score", "passed", "is_warning", "is_rejection", "rules_triggered"]

class QualityFailureSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityFailure
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class ProficiencyTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProficiencyTest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
