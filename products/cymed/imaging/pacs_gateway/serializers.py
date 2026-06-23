from rest_framework import serializers
from .models import PACSNode, PACSQuery, StudyRoute, PACSEvent


class PACSNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PACSNode
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PACSQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = PACSQuery
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StudyRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyRoute
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PACSEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PACSEvent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
