from rest_framework import serializers

from products.cyed.timetable.models import TimetableSlot


class TimetableSlotSerializer(serializers.ModelSerializer):
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")
    teacher_display = serializers.SerializerMethodField()

    class Meta:
        model = TimetableSlot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_teacher_display(self, obj) -> str:
        return obj.teacher_display()

    def validate_teacher(self, staff):
        """
        Refuse to timetable someone whose WWCC or teacher registration has
        lapsed, or was never recorded.

        Enforced at assignment rather than reported at audit: in Australia an
        expired clearance must stop classroom contact, and a system that only
        flags it afterwards has not met the obligation.
        """
        if staff is None:
            return staff
        from products.cyed.hr.compliance import ComplianceError, assert_may_teach

        try:
            assert_may_teach(staff)
        except ComplianceError as exc:
            raise serializers.ValidationError(str(exc))
        return staff

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        # Conflict detection: no double-booking of a room or teacher in an
        # overlapping time window on the same day (same tenant).
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None) if request else None
        day = attrs.get("day_of_week", getattr(self.instance, "day_of_week", None))
        room = attrs.get("room", getattr(self.instance, "room", ""))

        # Prefer the real teacher link over the free-text name: two staff who
        # happen to share a name (or "A. Nguyen" vs "Anh Nguyen" typed
        # differently) must not be silently treated as different people, and
        # must not be silently treated as the same person either once they're
        # properly linked. Fall back to name-matching only for legacy rows
        # that have never been backfilled to a Staff record.
        teacher_fk = attrs.get("teacher", getattr(self.instance, "teacher", None))
        class_section = attrs.get("class_section", getattr(self.instance, "class_section", None))
        effective_teacher_id = teacher_fk.id if teacher_fk else (
            class_section.teacher_id if class_section and not teacher_fk else None
        )
        teacher_name = attrs.get("teacher_name", getattr(self.instance, "teacher_name", ""))

        if tenant_id and day and start and end:
            qs = TimetableSlot.objects.filter(
                tenant_id=tenant_id, day_of_week=day,
                start_time__lt=end, end_time__gt=start,
            )
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if room and qs.filter(room=room).exists():
                raise serializers.ValidationError(
                    {"room": f"Room '{room}' is already booked in this time window on {day}."}
                )
            if effective_teacher_id and qs.filter(teacher_id=effective_teacher_id).exists():
                raise serializers.ValidationError(
                    {"teacher": "This teacher is already timetabled in this window on {}.".format(day)}
                )
            elif not effective_teacher_id and teacher_name and qs.filter(
                teacher__isnull=True, teacher_name=teacher_name
            ).exists():
                raise serializers.ValidationError(
                    {"teacher_name": f"{teacher_name} is already timetabled in this window on {day} "
                                      "(unlinked legacy record — link this teacher to hr.Staff to get "
                                      "reliable conflict detection)."}
                )
        return attrs
