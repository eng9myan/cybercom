from rest_framework import serializers

from products.cyed.staff_attendance.models import StaffAttendanceDay, Timesheet


class StaffAttendanceDaySerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    is_paid = serializers.BooleanField(read_only=True)
    hours_worked = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    minutes_late = serializers.IntegerField(read_only=True)

    class Meta:
        model = StaffAttendanceDay
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}" if obj.staff_id else ""

    def validate(self, attrs):
        # (tenant_id, staff, date) is unique but tenant_id is injected on save,
        # so enforce here for a clean 400 rather than a DB IntegrityError.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        staff = attrs.get("staff") or getattr(self.instance, "staff", None)
        date = attrs.get("date") or getattr(self.instance, "date", None)
        qs = StaffAttendanceDay.objects.filter(tenant_id=tenant_id, staff=staff, date=date)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An attendance record already exists for this staff member and date.")
        check_in = attrs.get("check_in")
        check_out = attrs.get("check_out")
        if check_in and check_out and check_out == check_in:
            raise serializers.ValidationError({"check_out": "Check-out must differ from check-in."})
        return attrs


class TimesheetSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = Timesheet
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "total_hours", "days_present", "days_absent", "days_leave", "total_minutes_late",
        ]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}" if obj.staff_id else ""

    def validate(self, attrs):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        staff = attrs.get("staff") or getattr(self.instance, "staff", None)
        label = attrs.get("period_label") or getattr(self.instance, "period_label", None)
        qs = Timesheet.objects.filter(tenant_id=tenant_id, staff=staff, period_label=label)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A timesheet already exists for this staff member and period.")
        start = attrs.get("period_start") or getattr(self.instance, "period_start", None)
        end = attrs.get("period_end") or getattr(self.instance, "period_end", None)
        if start and end and end < start:
            raise serializers.ValidationError({"period_end": "Period end cannot be before period start."})
        return attrs
