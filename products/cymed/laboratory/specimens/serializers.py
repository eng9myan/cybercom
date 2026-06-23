from rest_framework import serializers
from .models import Specimen, SpecimenContainer, SpecimenCollection, SpecimenTransport, SpecimenStorage, SpecimenRejection, SpecimenChainOfCustody

class SpecimenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specimen
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SpecimenContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecimenContainer
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SpecimenCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecimenCollection
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SpecimenTransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecimenTransport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SpecimenStorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecimenStorage
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SpecimenRejectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecimenRejection
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SpecimenChainOfCustodySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecimenChainOfCustody
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
