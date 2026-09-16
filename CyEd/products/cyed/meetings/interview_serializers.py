from rest_framework import serializers

from products.cyed.meetings.models import InterviewBooking, InterviewRound, InterviewSlot


class InterviewRoundSerializer(serializers.ModelSerializer):
    is_open = serializers.SerializerMethodField()
    slot_count = serializers.SerializerMethodField()

    class Meta:
        model = InterviewRound
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_is_open(self, obj) -> bool:
        return obj.is_open()

    def get_slot_count(self, obj) -> int:
        return obj.slots.count()

    def validate(self, attrs):
        opens = attrs.get("bookings_open_at", getattr(self.instance, "bookings_open_at", None))
        closes = attrs.get("bookings_close_at", getattr(self.instance, "bookings_close_at", None))
        if opens and closes and closes <= opens:
            raise serializers.ValidationError({
                "bookings_close_at": "Bookings must close after they open."
            })
        return attrs


class InterviewSlotSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    ends_at = serializers.SerializerMethodField()
    is_booked = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSlot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_teacher_name(self, obj) -> str:
        return f"{obj.teacher.first_name} {obj.teacher.last_name}".strip() if obj.teacher_id else ""

    def get_ends_at(self, obj):
        return obj.ends_at()

    def get_is_booked(self, obj) -> bool:
        return obj.bookings.filter(status="booked").exists()


class InterviewBookingSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    starts_at = serializers.DateTimeField(source="slot.starts_at", read_only=True)
    location = serializers.CharField(source="slot.location", read_only=True)

    class Meta:
        model = InterviewBooking
        fields = "__all__"
        # Booking and cancelling are actions: the fairness rules, the per-round
        # cap and the double-booking guard all live there, and a PATCHable
        # `status` would route around every one of them.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at", "slot", "student",
            "booked_by_email", "booked_by_name", "status", "cancelled_at",
        ]

    def get_teacher_name(self, obj) -> str:
        teacher = obj.slot.teacher if obj.slot_id else None
        return f"{teacher.first_name} {teacher.last_name}".strip() if teacher else ""

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""
