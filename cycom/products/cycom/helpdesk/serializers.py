from rest_framework import serializers

from products.cycom.helpdesk.models import SLAPolicy, Ticket


class SLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAPolicy
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TicketSerializer(serializers.ModelSerializer):
    is_breached = serializers.BooleanField(read_only=True)
    sla_policy_name = serializers.CharField(source="sla_policy.name", read_only=True, default="")

    class Meta:
        model = Ticket
        fields = [
            "id", "number", "subject", "customer_name", "assignee", "team",
            "priority", "stage", "description", "sla_policy", "sla_policy_name",
            "sla_deadline", "resolved_at", "is_breached", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "tenant_id", "sla_policy", "sla_deadline", "resolved_at",
            "created_at", "updated_at",
        ]
