"""CyMed Pharmacy Delivery serializers."""
from rest_framework import serializers

from .models import Courier, DeliveryJob, DeliveryStatusEvent, Rider


class CourierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = "__all__"


class RiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rider
        fields = "__all__"


class DeliveryJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryJob
        fields = "__all__"


class DeliveryStatusEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryStatusEvent
        fields = "__all__"
