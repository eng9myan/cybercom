from rest_framework import serializers

from products.cycom.crm.models import Activity, Lead


class ActivitySerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source="get_activity_type_display", read_only=True)

    class Meta:
        model = Activity
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LeadSerializer(serializers.ModelSerializer):
    open_activities = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_open_activities(self, obj) -> int:
        return obj.activities.filter(done=False).count()
