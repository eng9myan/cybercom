import uuid

from rest_framework import serializers

from products.cymed.clinic.telemedicine.models import (
    VirtualConsent,
    VirtualRecording,
    VirtualSession,
    VirtualVisit,
)


class VirtualRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualRecording
        fields = "__all__"


class VirtualSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualSession
        fields = ["session_token", "connection_url", "started_at", "ended_at"]


class VirtualConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualConsent
        fields = ["id", "patient", "consented_at", "signature_blob", "is_active"]
        read_only_fields = ["consented_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)


class VirtualVisitSerializer(serializers.ModelSerializer):
    session = VirtualSessionSerializer(read_only=True)

    class Meta:
        model = VirtualVisit
        fields = ["id", "patient", "provider_id", "scheduled_start", "status", "session"]

    def create(self, validated_data):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        validated_data["tenant_id"] = tenant_id

        visit = super().create(validated_data)

        # Generate connection URL mock
        session_token = str(uuid.uuid4())
        connection_url = f"https://cyconnect.cymed.io/meeting/{session_token}"

        VirtualSession.objects.create(
            tenant_id=tenant_id,
            visit=visit,
            session_token=session_token,
            connection_url=connection_url,
        )

        return visit
