from rest_framework import serializers

from products.cymed.hospital.bed_management.models import (
    BedAssignment,
    BedBlocking,
    BedCleaning,
    BedMaintenance,
    BedOccupancy,
    BedReservation,
)


class BedAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedAssignment
        fields = ["id", "patient", "bed", "assigned_at", "released_at"]
        read_only_fields = ["assigned_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        assignment = super().create(validated_data)

        # Update core Bed model occupancy status via direct property or service (normally core bed status)
        bed = assignment.bed
        bed.status = "occupied"
        bed.save()

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.hospital.bed.assigned",
            aggregate_type="BedAssignment",
            aggregate_id=assignment.id,
            tenant_id=tenant_id,
            payload={
                "bed_assignment_id": str(assignment.id),
                "patient_id": str(assignment.patient.id),
                "bed_id": str(assignment.bed.id),
                "assigned_at": assignment.assigned_at.isoformat(),
            },
        )

        # Trigger ERP Billing Charge Event
        canonical_events.emit(
            event_type="cymed.charge.created",
            aggregate_type="BillingCharge",
            aggregate_id=assignment.id,
            tenant_id=tenant_id,
            payload={
                "bed_assignment_id": str(assignment.id),
                "charge_type": "bed_occupancy",
                "amount": 300.00,
                "currency": "AED",
                "service_code": "BED-OCC-01",
            },
        )

        return assignment


class BedOccupancySerializer(serializers.ModelSerializer):
    class Meta:
        model = BedOccupancy
        fields = "__all__"


class BedReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedReservation
        fields = "__all__"


class BedCleaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedCleaning
        fields = "__all__"


class BedMaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedMaintenance
        fields = "__all__"


class BedBlockingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedBlocking
        fields = "__all__"
