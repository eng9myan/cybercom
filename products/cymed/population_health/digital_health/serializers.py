from rest_framework import serializers
from .models import (
    NationalHealthID,
    VaccinationCertificate,
    HealthPass,
    DigitalHealthWalletEntry,
)


class NationalHealthIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalHealthID
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class VaccinationCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VaccinationCertificate
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class HealthPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthPass
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DigitalHealthWalletEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalHealthWalletEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
