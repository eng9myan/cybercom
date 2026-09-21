from rest_framework import serializers

from products.cycom.events.models import Event, Registration, TicketType


class TicketTypeSerializer(serializers.ModelSerializer):
    registered_count = serializers.IntegerField(read_only=True)
    is_sold_out = serializers.BooleanField(read_only=True)

    class Meta:
        model = TicketType
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "checked_in_at", "created_at", "updated_at"]


class EventSerializer(serializers.ModelSerializer):
    ticket_types = TicketTypeSerializer(many=True, read_only=True)
    registered_count = serializers.IntegerField(read_only=True)
    is_sold_out = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
