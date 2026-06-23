from rest_framework import serializers

from .models import (
    DocumentationTemplate,
    SmartPhrase,
    ProviderClinicalNote,
    NoteCoSignature,
    VoiceDictation,
)


class DocumentationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentationTemplate
        fields = '__all__'


class SmartPhraseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartPhrase
        fields = '__all__'


class NoteCoSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteCoSignature
        fields = '__all__'


class VoiceDictationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceDictation
        fields = '__all__'


class ProviderClinicalNoteSerializer(serializers.ModelSerializer):
    cosignatures = NoteCoSignatureSerializer(many=True, read_only=True)
    dictations = VoiceDictationSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderClinicalNote
        fields = '__all__'
