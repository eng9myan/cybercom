from rest_framework import serializers
from products.cymed.core.encounters.models import (
    Encounter, EncounterParticipant, EncounterDiagnosis, EpisodeOfCare
)

class EncounterParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncounterParticipant
        fields = ["id", "provider", "role"]

class EncounterDiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncounterDiagnosis
        fields = ["id", "condition_code", "display", "use"]

class EncounterSerializer(serializers.ModelSerializer):
    participants = EncounterParticipantSerializer(many=True, required=False)
    diagnoses = EncounterDiagnosisSerializer(many=True, required=False)

    class Meta:
        model = Encounter
        fields = [
            "id", "patient", "episode_of_care", "encounter_type", "status",
            "start_time", "end_time", "organization", "facility",
            "participants", "diagnoses", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        participants_data = validated_data.pop("participants", [])
        diagnoses_data = validated_data.pop("diagnoses", [])

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        enc = Encounter.objects.create(**validated_data)

        for p_data in participants_data:
            EncounterParticipant.objects.create(encounter=enc, tenant_id=enc.tenant_id, **p_data)
        for d_data in diagnoses_data:
            EncounterDiagnosis.objects.create(encounter=enc, tenant_id=enc.tenant_id, **d_data)

        # Publish outbox event
        from platform.events.models import OutboxEvent
        OutboxEvent.objects.create(
            tenant_id=enc.tenant_id,
            topic="cymed.encounter.events",
            event_type="cymed.encounter.created",
            payload={
                "encounter_id": str(enc.id),
                "patient_id": str(enc.patient.id),
                "encounter_type": enc.encounter_type,
                "status": enc.status
            }
        )

        return enc


class EpisodeOfCareSerializer(serializers.ModelSerializer):
    class Meta:
        model = EpisodeOfCare
        fields = ["id", "patient", "status", "start_time", "end_time", "managing_organization"]
