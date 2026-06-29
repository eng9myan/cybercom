from rest_framework import serializers

from products.cymed.core.patients.models import (
    Patient,
    PatientAddress,
    PatientCommunication,
    PatientContact,
    PatientIdentifier,
)


class PatientIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientIdentifier
        fields = ["id", "system", "value", "use"]


class PatientContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientContact
        fields = ["id", "telecom_system", "telecom_value", "use"]


class PatientAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientAddress
        fields = ["id", "line1", "line2", "city", "state", "postal_code", "country", "use"]


class PatientCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientCommunication
        fields = ["id", "language_code", "preferred"]


class PatientSerializer(serializers.ModelSerializer):
    identifiers = PatientIdentifierSerializer(many=True, required=False)
    contacts = PatientContactSerializer(many=True, required=False)
    addresses = PatientAddressSerializer(many=True, required=False)
    communications = PatientCommunicationSerializer(many=True, required=False)

    class Meta:
        model = Patient
        fields = [
            "id",
            "first_name",
            "last_name",
            "dob",
            "gender",
            "mrn",
            "national_id",
            "passport_number",
            "is_active",
            "merged_into",
            "identifiers",
            "contacts",
            "addresses",
            "communications",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["mrn", "merged_into", "created_at", "updated_at"]

    def create(self, validated_data):
        identifiers_data = validated_data.pop("identifiers", [])
        contacts_data = validated_data.pop("contacts", [])
        addresses_data = validated_data.pop("addresses", [])
        communications_data = validated_data.pop("communications", [])

        # Auto-inject MRN and tenant_id from request
        from products.cymed.core.patients.services import PatientService

        validated_data["mrn"] = PatientService.generate_mrn()
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        patient = Patient.objects.create(**validated_data)

        # Create nested items
        for id_data in identifiers_data:
            PatientIdentifier.objects.create(
                patient=patient, tenant_id=patient.tenant_id, **id_data
            )
        for contact_data in contacts_data:
            PatientContact.objects.create(
                patient=patient, tenant_id=patient.tenant_id, **contact_data
            )
        for addr_data in addresses_data:
            PatientAddress.objects.create(patient=patient, tenant_id=patient.tenant_id, **addr_data)
        for comm_data in communications_data:
            PatientCommunication.objects.create(
                patient=patient, tenant_id=patient.tenant_id, **comm_data
            )

        # Publish patient created event
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=patient.tenant_id,
            topic="cymed.patient.events",
            event_type="cymed.patient.created",
            payload={"patient_id": str(patient.id), "mrn": patient.mrn},
        )

        return patient


class PatientMergeSerializer(serializers.Serializer):
    source_patient_id = serializers.UUIDField()
    target_patient_id = serializers.UUIDField()


class PatientUnmergeSerializer(serializers.Serializer):
    merge_history_id = serializers.UUIDField()
