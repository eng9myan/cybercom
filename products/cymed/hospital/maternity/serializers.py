from rest_framework import serializers
from products.cymed.hospital.maternity.models import Pregnancy, PrenatalEncounter, LaborEpisode, Delivery, NewbornRecord, PostpartumCare
from platform.events.models import OutboxEvent

class PregnancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pregnancy
        fields = "__all__"

class PrenatalEncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrenatalEncounter
        fields = "__all__"

class LaborEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaborEpisode
        fields = "__all__"

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ["id", "labor_episode", "delivery_time", "delivery_method", "apgar_1m", "apgar_5m", "outcome"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        delivery = super().create(validated_data)

        # Trigger Delivery charge
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(delivery.labor_episode.pregnancy.patient.id), # Patient level tracking
                "charge_type": "labor_delivery",
                "amount": 1800.00,
                "currency": "AED",
                "service_code": "MAT-DEL-01"
            }
        )

        return delivery

class NewbornRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewbornRecord
        fields = ["id", "delivery", "baby_patient", "gender", "weight_grams", "height_cm", "head_circumference_cm"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        
        # Auto-create core patient for newborn if not supplied
        if not validated_data.get("baby_patient"):
            from products.cymed.core.patients.models import Patient
            import random
            mrn_val = f"MRN-NB-{random.randint(10000, 99999)}"
            baby = Patient.objects.create(
                tenant_id=tenant_id,
                first_name="Newborn",
                last_name="Baby",
                dob=validated_data["delivery"].delivery_time.date(),
                gender=validated_data.get("gender", "unknown"),
                mrn=mrn_val
            )
            validated_data["baby_patient"] = baby

        newborn = super().create(validated_data)
        return newborn

class PostpartumCareSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostpartumCare
        fields = "__all__"
