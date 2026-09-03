"""DRF serializers for prep templates, assignments, checklist items, and consent."""
from __future__ import annotations

from rest_framework import serializers

from .models import ContrastConsent, PrepAssignment, PrepChecklistItem, PrepTemplate


class PrepTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrepTemplate
        fields = "__all__"


class PrepAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrepAssignment
        fields = "__all__"


class PrepChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrepChecklistItem
        fields = "__all__"


class ContrastConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContrastConsent
        fields = "__all__"
