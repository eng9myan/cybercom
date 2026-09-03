from rest_framework import serializers

from products.cycom.helpdesk.models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id", "number", "subject", "customer_name", "assignee", "team",
            "priority", "stage", "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
