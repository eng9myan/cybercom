from rest_framework import serializers

from products.cyed.attendance.models import (
    AbsenceExplanation,
    AttendanceMark,
    EmergencyDrill,
    LatePass,
    RollCall,
)


class EmergencyDrillSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyDrill
        fields = "__all__"
        # The whole lifecycle moves through actions so the roll is snapshotted
        # and the closing count cannot be edited after the fact.
        read_only_fields = [f.name for f in EmergencyDrill._meta.fields]

    def get_duration_seconds(self, obj):
        return obj.duration_seconds()

    def get_is_open(self, obj) -> bool:
        return obj.is_open()


class AbsenceExplanationSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    day_count = serializers.SerializerMethodField()

    class Meta:
        model = AbsenceExplanation
        fields = "__all__"
        # Everything about the review is set by the accept/decline actions, and
        # the submitter is stamped from the token — a family cannot mark their
        # own explanation accepted, which would defeat the point of review.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at", "status",
            "submitted_by_email", "submitted_by_name",
            "reviewed_by", "reviewed_on", "review_note", "marks_updated",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_day_count(self, obj) -> int:
        return obj.day_count()

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "The last day cannot be before the first."}
            )
        if start and end and (end - start).days > 30:
            # A month-long absence is a withdrawal conversation with the office,
            # not a portal form — and an unbounded range would let one
            # submission excuse a year of marks.
            raise serializers.ValidationError(
                {"end_date": "Explanations cover at most 31 days. Contact the office for longer."}
            )
        return attrs


class RollCallSerializer(serializers.ModelSerializer):
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")
    # period_label is part of the (class_section, date, period_label) uniqueness
    # constraint, which otherwise makes DRF require it. A daily roll call may have
    # no period, so default it to "" and keep it optional.
    period_label = serializers.CharField(required=False, allow_blank=True, default="")
    present_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()

    class Meta:
        model = RollCall
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_present_count(self, obj) -> int:
        return obj.marks.filter(status="present").count()

    def get_absent_count(self, obj) -> int:
        return obj.marks.filter(status="absent").count()


class AttendanceMarkSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    # The date and class the mark belongs to. Carried on the mark because the
    # question asked of a mark is almost always "which day was this?" — without
    # it every reader has to fetch roll calls separately and join them, which a
    # parent portal cannot do reliably once a school has thousands of them.
    date = serializers.DateField(source="roll_call.date", read_only=True)
    class_section_name = serializers.CharField(
        source="roll_call.class_section.name", read_only=True, default=""
    )
    period_label = serializers.CharField(
        source="roll_call.period_label", read_only=True, default=""
    )

    class Meta:
        model = AttendanceMark
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip()


class LatePassSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")
    pass_number = serializers.CharField(read_only=True)

    class Meta:
        model = LatePass
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "printed_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip()
