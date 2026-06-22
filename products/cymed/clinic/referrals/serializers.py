from rest_framework import serializers
from products.cymed.clinic.referrals.models import Referral, ReferralReason, ReferralProvider, ReferralAttachment
from platform.events.models import OutboxEvent

class ReferralReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralReason
        fields = "__all__"

class ReferralProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralProvider
        fields = "__all__"

class ReferralAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralAttachment
        fields = ["id", "title", "file_url"]

class ReferralSerializer(serializers.ModelSerializer):
    attachments = ReferralAttachmentSerializer(many=True, required=False)

    class Meta:
        model = Referral
        fields = ["id", "patient", "referred_by", "target_provider", "reason", "status", "notes", "created_at", "attachments"]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        validated_data["tenant_id"] = tenant_id

        attachments_data = validated_data.pop("attachments", [])
        referral = Referral.objects.create(**validated_data)

        for a in attachments_data:
            ReferralAttachment.objects.create(tenant_id=tenant_id, referral=referral, **a)

        # Publish Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.clinic.events",
            event_type="cymed.clinic.referral.created",
            payload={
                "referral_id": str(referral.id),
                "patient_id": str(referral.patient.id),
                "target_provider_id": str(referral.target_provider.id),
                "referred_by": referral.referred_by,
                "timestamp": referral.created_at.isoformat()
            }
        )

        return referral
