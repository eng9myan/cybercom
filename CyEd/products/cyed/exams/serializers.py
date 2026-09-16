from rest_framework import serializers

from products.cyed.exams.models import ExamCandidate, ExamRoom, ExamRoomAllocation, ExamSitting


class ExamRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamRoom
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        rows = attrs.get("rows", getattr(self.instance, "rows", 1))
        columns = attrs.get("columns", getattr(self.instance, "columns", 1))
        capacity = attrs.get("capacity", getattr(self.instance, "capacity", 0))
        if capacity > rows * columns:
            raise serializers.ValidationError({
                "capacity": (
                    f"The grid is {rows}×{columns} = {rows * columns} desks, which cannot "
                    f"seat {capacity}. Seats would be allocated that do not exist."
                )
            })
        return attrs


class ExamRoomAllocationSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source="room.name", read_only=True)
    capacity = serializers.IntegerField(source="room.capacity", read_only=True)

    class Meta:
        model = ExamRoomAllocation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ExamCandidateSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    room_name = serializers.CharField(source="room.name", read_only=True, default="")

    class Meta:
        model = ExamCandidate
        fields = "__all__"
        # Seating and tickets are produced by the allocator, not typed in: a
        # hand-edited seat is how two students end up at one desk.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "room", "seat_label", "ticket_number", "ticket_issued_on",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""


class ExamSittingSerializer(serializers.ModelSerializer):
    room_allocations = ExamRoomAllocationSerializer(many=True, read_only=True)
    candidate_count = serializers.SerializerMethodField()
    seats_available = serializers.SerializerMethodField()

    class Meta:
        model = ExamSitting
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "status"]

    def get_candidate_count(self, obj) -> int:
        return obj.candidates.count()

    def get_seats_available(self, obj) -> int:
        return obj.total_capacity()
