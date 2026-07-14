from rest_framework import serializers

from .models import DigitalCard, HealthPass, HealthWallet, VaccinationRecord


class HealthWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthWallet
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "card_count"]


class DigitalCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalCard
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class HealthPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthPass
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class VaccinationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VaccinationRecord
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
