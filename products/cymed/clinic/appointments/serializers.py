from rest_framework import serializers
from products.cymed.clinic.appointments.models import ClinicAppointment, AppointmentReminder, AppointmentWaitlist, AppointmentTemplate, AppointmentRule
from products.cymed.core.scheduling.models import Appointment, AppointmentParticipant
from django.utils import timezone

class AppointmentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentTemplate
        fields = "__all__"

class AppointmentRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentRule
        fields = "__all__"

class ClinicAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicAppointment
        fields = ["id", "appointment", "specialty_code", "checkin_status", "source"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        # Enforce Conflict Rules Check
        appt = validated_data["appointment"]
        specialty = validated_data["specialty_code"]
        
        rule = AppointmentRule.objects.filter(
            tenant_id=validated_data["tenant_id"],
            specialty_code=specialty
        ).first()
        
        if rule and not rule.allow_conflicting_bookings:
            # Check for double booking of participants in the core scheduling system
            participants = appt.participants.all()
            for p in participants:
                conflicts = AppointmentParticipant.objects.filter(
                    tenant_id=validated_data["tenant_id"],
                    actor_id=p.actor_id,
                    actor_type=p.actor_type,
                    appointment__start_time__lt=appt.end_time,
                    appointment__end_time__gt=appt.start_time
                ).exclude(appointment=appt)
                
                if conflicts.exists():
                    raise serializers.ValidationError(
                        f"Participant {p.actor_id} has a conflicting appointment."
                    )

        clinic_appt = super().create(validated_data)

        # Queue automated reminder via CyConnect mock
        AppointmentReminder.objects.create(
            tenant_id=clinic_appt.tenant_id,
            clinic_appointment=clinic_appt,
            channel="sms",
            scheduled_time=appt.start_time - timezone.timedelta(hours=24),
            status="pending"
        )

        return clinic_appt

class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = "__all__"

class AppointmentWaitlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentWaitlist
        fields = "__all__"
