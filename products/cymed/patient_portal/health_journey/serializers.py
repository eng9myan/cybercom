from rest_framework import serializers

from .models import (
    CareEpisode,
    HealthMilestone,
    HealthTimeline,
    HealthTimelineEvent,
    PatientJourney,
)


class HealthTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthTimeline
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "last_updated"]


class HealthTimelineEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthTimelineEvent
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PatientJourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientJourney
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class HealthMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthMilestone
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CareEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareEpisode
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
