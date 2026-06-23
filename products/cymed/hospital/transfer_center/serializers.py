from rest_framework import serializers
from products.cymed.hospital.transfer_center.models import ReceivingFacility, TransferCase, ExternalReferral, AcceptanceReview
from platform.events.models import OutboxEvent

class ReceivingFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceivingFacility
        fields = "__all__"

class TransferCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferCase
        fields = ["id", "patient", "source_hospital_name", "target_facility", "status", "reason"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        tcase = super().create(validated_data)

        # Trigger Hospital Transfer Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.hospital.events",
            event_type="cymed.hospital.transfer.created",
            payload={
                "transfer_case_id": str(tcase.id),
                "patient_id": str(tcase.patient.id),
                "source": tcase.source_hospital_name,
                "target": tcase.target_facility.name,
                "reason": tcase.reason
            }
        )

        # Trigger ERP Procurement for ambulance / transit services
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.procurement.events",
            event_type="cymed.procurement.requested",
            payload={
                "encounter_id": str(tcase.id),
                "item_code": "AMB-TRANS-SERV",
                "quantity": 1,
                "requestor": "TransferCenter"
            }
        )

        return tcase

class ExternalReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalReferral
        fields = "__all__"

class AcceptanceReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcceptanceReview
        fields = ["id", "transfer_case", "reviewed_by", "reviewed_at", "decision", "notes"]
        read_only_fields = ["reviewed_at"]

    def create(self, validated_data):
        review = super().create(validated_data)

        # Update TransferCase status based on decision
        tcase = review.transfer_case
        if review.decision == "accept":
            tcase.status = "accepted"
        else:
            tcase.status = "rejected"
        tcase.save()

        return review
