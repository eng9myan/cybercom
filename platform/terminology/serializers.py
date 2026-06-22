from rest_framework import serializers
from platform.terminology.models import TerminologyAuditLog

class TerminologyAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TerminologyAuditLog
        fields = "__all__"

class TerminologySearchSerializer(serializers.Serializer):
    provider = serializers.CharField()
    tenant_id = serializers.UUIDField()
    query = serializers.CharField()
    limit = serializers.IntegerField(default=10, required=False)

class TerminologyLookupSerializer(serializers.Serializer):
    provider = serializers.CharField()
    tenant_id = serializers.UUIDField()
    code = serializers.CharField()
    system = serializers.CharField(required=False, allow_blank=True)

class TerminologyValidateSerializer(serializers.Serializer):
    provider = serializers.CharField()
    tenant_id = serializers.UUIDField()
    code = serializers.CharField()
    system = serializers.CharField(required=False, allow_blank=True)
    value_set = serializers.CharField(required=False, allow_blank=True)

class TerminologyTranslateSerializer(serializers.Serializer):
    provider = serializers.CharField()
    tenant_id = serializers.UUIDField()
    code = serializers.CharField()
    target_system = serializers.CharField()
    concept_map = serializers.CharField(required=False, allow_blank=True)

class TerminologyExpandSerializer(serializers.Serializer):
    provider = serializers.CharField()
    tenant_id = serializers.UUIDField()
    value_set = serializers.CharField()
    filter_str = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class TerminologySubsumesSerializer(serializers.Serializer):
    provider = serializers.CharField()
    tenant_id = serializers.UUIDField()
    code_a = serializers.CharField()
    code_b = serializers.CharField()
    system = serializers.CharField(required=False, allow_blank=True)

