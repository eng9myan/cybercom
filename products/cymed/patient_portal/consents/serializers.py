from rest_framework import serializers

from .models import (
    ConsentHistory,
    ConsentRequest,
    PortalConsentRecord,
    PortalConsentType,
)


class PortalConsentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalConsentType
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ConsentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentHistory
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "changed_at"]


class PortalConsentRecordSerializer(serializers.ModelSerializer):
    consent_type_detail = PortalConsentTypeSerializer(source="consent_type", read_only=True)
    history = ConsentHistorySerializer(many=True, read_only=True)

    class Meta:
        model = PortalConsentRecord
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PortalConsentRecordWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalConsentRecord
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ConsentRequestSerializer(serializers.ModelSerializer):
    consent_type_detail = PortalConsentTypeSerializer(source="consent_type", read_only=True)

    class Meta:
        model = ConsentRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "requested_at"]
