from rest_framework import serializers

from core.serializers import ReadOnlyModelSerializer

from products.cyed.docsign.models import SignableDocument, Signatory, SignatureAuditEvent


class SignatorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Signatory
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "signed_at", "signed_hash", "ip_address",
        ]


class SignatureAuditEventSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = SignatureAuditEvent
        fields = "__all__"


class SignableDocumentSerializer(serializers.ModelSerializer):
    signatories = SignatorySerializer(many=True, read_only=True)
    signed_count = serializers.IntegerField(read_only=True)
    pending_count = serializers.IntegerField(read_only=True)
    verified = serializers.SerializerMethodField()

    class Meta:
        model = SignableDocument
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "sent_at", "completed_at", "content_hash",
        ]

    def get_verified(self, obj):
        return obj.verify()
