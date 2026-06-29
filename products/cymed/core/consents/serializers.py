from rest_framework import serializers

from products.cymed.core.consents.models import Consent, ConsentSignature


class ConsentSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentSignature
        fields = ["id", "signatory_name", "signature_image_url", "signed_at"]


class ConsentSerializer(serializers.ModelSerializer):
    signature = ConsentSignatureSerializer(required=False)

    class Meta:
        model = Consent
        fields = [
            "id",
            "patient",
            "category",
            "status",
            "policy_rule",
            "start_time",
            "end_time",
            "signature",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        sig_data = validated_data.pop("signature", None)

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        consent = Consent.objects.create(**validated_data)

        if sig_data:
            ConsentSignature.objects.create(
                consent=consent, tenant_id=consent.tenant_id, **sig_data
            )

        # Publish outbox event
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=consent.tenant_id,
            topic="cymed.consent.events",
            event_type="cymed.consent.created",
            payload={
                "consent_id": str(consent.id),
                "patient_id": str(consent.patient.id),
                "category": consent.category,
            },
        )

        return consent
