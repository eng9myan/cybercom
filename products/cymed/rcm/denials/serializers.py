from rest_framework import serializers
from .models import Denial, DenialReason, Appeal, AppealOutcome, CorrectiveAction


class DenialReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenialReason
        fields = "__all__"


class DenialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Denial
        fields = "__all__"


class AppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = "__all__"


class AppealOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppealOutcome
        fields = "__all__"


class CorrectiveActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrectiveAction
        fields = "__all__"
