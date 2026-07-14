from rest_framework import serializers

from platform.cydata.models import (
    CDCPipelineLog,
    DataAsset,
    DataLineage,
    DataQualityRule,
    MasterDataMap,
)


class DataAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataAsset
        fields = "__all__"


class DataLineageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataLineage
        fields = "__all__"


class DataQualityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataQualityRule
        fields = "__all__"


class MasterDataMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterDataMap
        fields = "__all__"


class CDCPipelineLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CDCPipelineLog
        fields = "__all__"


class DataQualityEvaluateRequestSerializer(serializers.Serializer):
    records = serializers.ListField(child=serializers.DictField())


class MasterDataMatchRequestSerializer(serializers.Serializer):
    entity_type = serializers.CharField(max_length=100)
    source_system = serializers.CharField(max_length=100)
    source_id = serializers.CharField(max_length=255)
    matching_fields = serializers.JSONField(default=dict)
