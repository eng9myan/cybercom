from rest_framework import serializers

from platform.terminology.services import TerminologyService
from products.cymed.clinic.consultations.models import (
    Consultation,
    ConsultationAttachment,
    ConsultationDiagnosis,
    ConsultationFollowUp,
    ConsultationPlan,
    ConsultationProcedure,
)


def _phi_text(required=False):
    # EncryptedText (BinaryField storage) — keep it plain text through DRF.
    return serializers.CharField(required=required, allow_blank=True)


class ConsultationDiagnosisSerializer(serializers.ModelSerializer):
    display = _phi_text(required=True)

    class Meta:
        model = ConsultationDiagnosis
        fields = ["id", "code", "system", "display", "status"]

    def validate(self, attrs):
        code = attrs.get("code")
        system = attrs.get("system")
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")

        try:
            is_valid = TerminologyService.validate(
                provider=system,
                code=code,
                tenant_id=str(tenant_id),
                requested_by=str(request.user) if request else "system",
            )
        except Exception:
            is_valid = False

        if not is_valid:
            raise serializers.ValidationError(
                f"Invalid diagnosis code '{code}' for system '{system}'."
            )
        return attrs


class ConsultationProcedureSerializer(serializers.ModelSerializer):
    display = _phi_text(required=True)
    notes = _phi_text()

    class Meta:
        model = ConsultationProcedure
        fields = ["id", "code", "system", "display", "notes"]


class ConsultationPlanSerializer(serializers.ModelSerializer):
    instructions = _phi_text()
    prescriptions = serializers.JSONField(required=False)

    class Meta:
        model = ConsultationPlan
        fields = ["id", "instructions", "prescriptions"]


class ConsultationFollowUpSerializer(serializers.ModelSerializer):
    reason = _phi_text()

    class Meta:
        model = ConsultationFollowUp
        fields = ["id", "follow_up_date", "reason"]


class ConsultationAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationAttachment
        fields = ["id", "title", "file_url"]


class ConsultationSerializer(serializers.ModelSerializer):
    subjective = _phi_text()
    objective = _phi_text()
    assessment = _phi_text()
    plan = _phi_text()
    diagnoses = ConsultationDiagnosisSerializer(many=True, required=False)
    procedures = ConsultationProcedureSerializer(many=True, required=False)
    treatment_plan = ConsultationPlanSerializer(required=False)
    follow_ups = ConsultationFollowUpSerializer(many=True, required=False)
    attachments = ConsultationAttachmentSerializer(many=True, required=False)

    class Meta:
        model = Consultation
        fields = [
            "id",
            "encounter",
            "consulted_at",
            "consulted_by",
            "subjective",
            "objective",
            "assessment",
            "plan",
            "diagnoses",
            "procedures",
            "treatment_plan",
            "follow_ups",
            "attachments",
        ]
        read_only_fields = ["consulted_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        validated_data["tenant_id"] = tenant_id

        diagnoses_data = validated_data.pop("diagnoses", [])
        procedures_data = validated_data.pop("procedures", [])
        plan_data = validated_data.pop("treatment_plan", None)
        follow_ups_data = validated_data.pop("follow_ups", [])
        attachments_data = validated_data.pop("attachments", [])

        consultation = Consultation.objects.create(**validated_data)

        # Create relations
        for d in diagnoses_data:
            ConsultationDiagnosis.objects.create(
                tenant_id=tenant_id, consultation=consultation, **d
            )
        for p in procedures_data:
            ConsultationProcedure.objects.create(
                tenant_id=tenant_id, consultation=consultation, **p
            )
        if plan_data:
            ConsultationPlan.objects.create(
                tenant_id=tenant_id, consultation=consultation, **plan_data
            )
        for f in follow_ups_data:
            ConsultationFollowUp.objects.create(tenant_id=tenant_id, consultation=consultation, **f)
        for a in attachments_data:
            ConsultationAttachment.objects.create(
                tenant_id=tenant_id, consultation=consultation, **a
            )

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.clinic.consultation.created",
            aggregate_type="Consultation",
            aggregate_id=consultation.id,
            tenant_id=tenant_id,
            payload={
                "consultation_id": str(consultation.id),
                "encounter_id": str(consultation.encounter.id),
                "consulted_by": consultation.consulted_by,
                "timestamp": consultation.consulted_at.isoformat(),
            },
        )

        return consultation
