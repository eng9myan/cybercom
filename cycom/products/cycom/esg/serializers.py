from rest_framework import serializers

from products.cycom.esg.models import EmissionEntry, EmissionFactor


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class EmissionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "co2e_kg"]
