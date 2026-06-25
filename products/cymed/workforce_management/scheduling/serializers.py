from rest_framework import serializers
from .models import ShiftTemplate, RosterCycle, RosterSlot, SelfScheduleWindow, SlotQuota


class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RosterCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RosterCycle
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RosterSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = RosterSlot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SelfScheduleWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfScheduleWindow
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SlotQuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotQuota
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
