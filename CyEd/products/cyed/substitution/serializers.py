from rest_framework import serializers

from products.cyed.substitution.models import (
    ReliefAvailability,
    ReliefBooking,
    ReliefTeacher,
    SubstitutionAssignment,
    SubstitutionPlan,
)


class ReliefTeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    may_teach = serializers.SerializerMethodField()
    clearance_problems = serializers.SerializerMethodField()

    class Meta:
        model = ReliefTeacher
        fields = "__all__"
        # `verified_by` is stamped from the authenticated user: a self-asserted
        # verifier is not evidence that anybody sighted the card.
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "verified_by"]

    def get_full_name(self, obj) -> str:
        return obj.full_name()

    def get_may_teach(self, obj) -> bool:
        return obj.may_teach()

    def get_clearance_problems(self, obj) -> list:
        return obj.clearance_state()["problems"]

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", "active"))
        reason = attrs.get(
            "do_not_book_reason", getattr(self.instance, "do_not_book_reason", "")
        )
        if status == "do_not_book" and not (reason or "").strip():
            raise serializers.ValidationError({
                "do_not_book_reason": (
                    "Record why. A name that cannot be booked with no reason attached "
                    "is unanswerable when someone asks six months later."
                )
            })
        return attrs


class ReliefAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReliefAvailability
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReliefBookingSerializer(serializers.ModelSerializer):
    relief_teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = ReliefBooking
        fields = "__all__"
        # The whole lifecycle moves through actions so clearance and
        # double-booking checks cannot be bypassed by posting a row.
        read_only_fields = [f.name for f in ReliefBooking._meta.fields]

    def get_relief_teacher_name(self, obj) -> str:
        return obj.relief_teacher.full_name() if obj.relief_teacher_id else ""


class SubstitutionAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubstitutionAssignment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SubstitutionPlanSerializer(serializers.ModelSerializer):
    assignments = SubstitutionAssignmentSerializer(many=True, read_only=True)
    covered_count = serializers.ReadOnlyField()
    gap_count = serializers.ReadOnlyField()

    class Meta:
        model = SubstitutionPlan
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
