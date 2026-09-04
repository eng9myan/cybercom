import random

from rest_framework import serializers

from products.cymed.clinic.reception.models import (
    ArrivalMethod,
    CheckIn,
    CheckOut,
    PatientQueueTicket,
    VisitReason,
    VisitStatus,
)


class ArrivalMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArrivalMethod
        fields = ["id", "name", "code"]


class VisitReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitReason
        fields = ["id", "name", "code"]


class VisitStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitStatus
        fields = ["id", "name", "code"]


class PatientQueueTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientQueueTicket
        fields = ["id", "ticket_number", "status", "priority"]


class CheckInSerializer(serializers.ModelSerializer):
    queue_ticket = PatientQueueTicketSerializer(read_only=True)

    class Meta:
        model = CheckIn
        fields = [
            "id",
            "patient",
            "appointment",
            "arrival_method",
            "visit_reason",
            "status",
            "checkin_time",
            "queue_ticket",
        ]
        read_only_fields = ["checkin_time"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        checkin = super().create(validated_data)

        # Generate Token/Ticket
        rand_num = random.randint(100, 999)
        ticket_number = f"T-{rand_num}"

        PatientQueueTicket.objects.create(
            tenant_id=checkin.tenant_id,
            checkin=checkin,
            ticket_number=ticket_number,
            status="waiting",
            priority="routine",
        )

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.clinic.checkin.created",
            aggregate_type="CheckIn",
            aggregate_id=checkin.id,
            tenant_id=checkin.tenant_id,
            payload={
                "checkin_id": str(checkin.id),
                "patient_id": str(checkin.patient.id),
                "ticket_number": ticket_number,
                "timestamp": checkin.checkin_time.isoformat(),
            },
        )

        return checkin


class CheckOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckOut
        fields = ["id", "checkin", "checkout_time", "status"]
        read_only_fields = ["checkout_time"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        checkout = super().create(validated_data)

        # Move ticket to completed status
        ticket = PatientQueueTicket.objects.filter(checkin=checkout.checkin).first()
        if ticket:
            ticket.status = "completed"
            ticket.save()

        return checkout
