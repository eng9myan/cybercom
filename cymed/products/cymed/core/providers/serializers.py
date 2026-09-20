from rest_framework import serializers

from products.cymed.core.patients.models import Patient
from products.cymed.core.providers.models import (
    Provider,
    ProviderAvailability,
    ProviderLicense,
    ProviderRole,
    ProviderSpecialty,
)
from products.cymed.core.scheduling.models import Appointment


class ScheduleAppointmentSerializer(serializers.ModelSerializer):
    """Lean, provider-schedule-view shape — the generic AppointmentSerializer
    (scheduling/serializers.py) exposes `patient` as a bare FK id, not enough
    for a clinician glancing at their day."""

    patient_name = serializers.SerializerMethodField()
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)

    class Meta:
        model = Appointment
        fields = ["id", "patient", "patient_name", "patient_mrn", "appointment_type",
                  "status", "start_time", "end_time", "description"]

    def get_patient_name(self, obj) -> str:
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class PatientRosterSerializer(serializers.ModelSerializer):
    """Lean roster row — deliberately not the full PatientSerializer (no
    identifiers/contacts/addresses nesting), since a roster list is read many
    times per session and each PHI field decrypts on access."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    mrn = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = ["id", "first_name", "last_name", "mrn", "dob", "gender", "is_active"]


class ProviderSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderSpecialty
        fields = ["id", "specialty_code", "specialty_display"]


class ProviderRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderRole
        fields = ["id", "role_code", "organization_id"]


class ProviderAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAvailability
        fields = ["id", "day_of_week", "available_start_time", "available_end_time"]


class ProviderLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderLicense
        fields = ["id", "license_number", "state_issued", "expiry_date"]


class ProviderSerializer(serializers.ModelSerializer):
    specialties = ProviderSpecialtySerializer(many=True, required=False)
    roles = ProviderRoleSerializer(many=True, required=False)
    availability = ProviderAvailabilitySerializer(many=True, required=False)
    licenses = ProviderLicenseSerializer(many=True, required=False)

    class Meta:
        model = Provider
        fields = [
            "id",
            "user_id",
            "first_name",
            "last_name",
            "provider_type",
            "npi",
            "is_active",
            "specialties",
            "roles",
            "availability",
            "licenses",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        specialties_data = validated_data.pop("specialties", [])
        roles_data = validated_data.pop("roles", [])
        availability_data = validated_data.pop("availability", [])
        licenses_data = validated_data.pop("licenses", [])

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        provider = Provider.objects.create(**validated_data)

        # Create nested items
        for spec in specialties_data:
            ProviderSpecialty.objects.create(
                provider=provider, tenant_id=provider.tenant_id, **spec
            )
        for role in roles_data:
            ProviderRole.objects.create(provider=provider, tenant_id=provider.tenant_id, **role)
        for avail in availability_data:
            ProviderAvailability.objects.create(
                provider=provider, tenant_id=provider.tenant_id, **avail
            )
        for lic in licenses_data:
            ProviderLicense.objects.create(provider=provider, tenant_id=provider.tenant_id, **lic)

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.provider.created",
            aggregate_type="Provider",
            aggregate_id=provider.id,
            tenant_id=provider.tenant_id,
            payload={
                "provider_id": str(provider.id),
                "npi": provider.npi,
                "type": provider.provider_type,
            },
        )

        return provider
