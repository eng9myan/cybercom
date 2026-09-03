"""DRF serializers for the CyMed MRFF Ambient Scribe sub-app."""

from rest_framework import serializers

from .models import ClinicianEdit, ScribeSession, Summary, Transcript


class ScribeSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScribeSession
        fields = "__all__"


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = "__all__"


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = "__all__"


class ClinicianEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicianEdit
        fields = "__all__"
