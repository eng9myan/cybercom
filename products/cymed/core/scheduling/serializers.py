from rest_framework import serializers
from products.cymed.core.scheduling.models import Appointment, AppointmentParticipant, ScheduleSlot

class AppointmentParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentParticipant
        fields = ["id", "actor_id", "actor_type", "required", "status"]

class AppointmentSerializer(serializers.ModelSerializer):
    participants = AppointmentParticipantSerializer(many=True, required=False)

    class Meta:
        model = Appointment
        fields = ["id", "patient", "appointment_type", "status", "start_time", "end_time", "description", "participants", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        participants_data = validated_data.pop("participants", [])

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        appt = Appointment.objects.create(**validated_data)

        for p_data in participants_data:
            AppointmentParticipant.objects.create(appointment=appt, tenant_id=appt.tenant_id, **p_data)

        # Publish outbox event
        from platform.events.models import OutboxEvent
        OutboxEvent.objects.create(
            tenant_id=appt.tenant_id,
            topic="cymed.appointment.events",
            event_type="cymed.appointment.created",
            payload={
                "appointment_id": str(appt.id),
                "patient_id": str(appt.patient.id),
                "start_time": appt.start_time.isoformat(),
                "end_time": appt.end_time.isoformat()
            }
        )

        return appt


class ScheduleSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleSlot
        fields = ["id", "resource_id", "start_time", "end_time", "status"]
