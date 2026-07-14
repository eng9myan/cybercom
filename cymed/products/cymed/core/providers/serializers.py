from rest_framework import serializers

from products.cymed.core.providers.models import (
    Provider,
    ProviderAvailability,
    ProviderLicense,
    ProviderRole,
    ProviderSpecialty,
)


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

        # Publish event
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=provider.tenant_id,
            topic="cymed.provider.events",
            event_type="cymed.provider.created",
            payload={
                "provider_id": str(provider.id),
                "npi": provider.npi,
                "type": provider.provider_type,
            },
        )

        return provider
