from rest_framework import serializers

from .models import (
    ConsultRequest,
    ProviderTelemedicineSession,
    SecondOpinionRequest,
    TelemedicineDocument,
)


class TelemedicineDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineDocument
        fields = "__all__"


class ProviderTelemedicineSessionSerializer(serializers.ModelSerializer):
    documents = TelemedicineDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderTelemedicineSession
        fields = "__all__"


class ConsultRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultRequest
        fields = "__all__"


class SecondOpinionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondOpinionRequest
        fields = "__all__"
