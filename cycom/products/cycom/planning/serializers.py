from rest_framework import serializers

from products.cycom.planning.models import ShiftSlot


class ShiftSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSlot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
