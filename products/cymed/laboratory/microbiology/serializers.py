from rest_framework import serializers
from .models import Culture, Organism, Sensitivity, ResistanceProfile, MicrobiologyResult

class SensitivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensitivity
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class ResistanceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResistanceProfile
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class OrganismSerializer(serializers.ModelSerializer):
    sensitivities = SensitivitySerializer(many=True, read_only=True)
    resistance_profiles = ResistanceProfileSerializer(many=True, read_only=True)
    class Meta:
        model = Organism
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class CultureSerializer(serializers.ModelSerializer):
    organisms = OrganismSerializer(many=True, read_only=True)
    class Meta:
        model = Culture
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class MicrobiologyResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = MicrobiologyResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
