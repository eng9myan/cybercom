from rest_framework import serializers

from products.cycom.cyai_memory.models import MemoryQueryLog, QueryPlan


class QueryPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryPlan
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MemoryQueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryQueryLog
        fields = "__all__"


class AskQuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
