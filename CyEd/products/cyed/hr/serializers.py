from rest_framework import serializers

from products.cyed.hr.models import (
    Contract, LeaveEntitlement, OnboardingTask, PerformanceReview, Staff, StaffClearance, StaffLeave,
)


class StaffSerializer(serializers.ModelSerializer):
    may_teach = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_may_teach(self, obj):
        """
        Surfaced on the staff record itself so a timetabler sees the blocker
        before they try the assignment, not as a 400 afterwards.
        """
        from products.cyed.hr.compliance import may_teach

        return may_teach(obj)


class StaffClearanceSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = StaffClearance
        fields = "__all__"
        # `verified_by` is stamped from the authenticated user, never accepted
        # from the request — a self-asserted verifier is not evidence.
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "verified_by"]

    def get_status(self, obj):
        return obj.status()

    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry()

    def validate(self, attrs):
        issued = attrs.get("issued_on") or getattr(self.instance, "issued_on", None)
        expires = attrs.get("expires_on") or getattr(self.instance, "expires_on", None)
        if issued and expires and expires < issued:
            raise serializers.ValidationError(
                {"expires_on": "A clearance cannot expire before it was issued."}
            )
        return attrs


class LeaveEntitlementSerializer(serializers.ModelSerializer):
    accrued_to_date = serializers.SerializerMethodField()
    taken = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = LeaveEntitlement
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_accrued_to_date(self, obj):
        return str(obj.accrued_days())

    def get_taken(self, obj):
        return str(obj.taken_days())

    def get_balance(self, obj):
        return str(obj.balance())


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StaffLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffLeave
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PerformanceReviewSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceReview
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "acknowledged_at"]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}" if obj.staff_id else ""

    def validate(self, attrs):
        # (tenant_id, staff, review_period) is unique; tenant is injected on save.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        staff = attrs.get("staff") or getattr(self.instance, "staff", None)
        period = attrs.get("review_period") or getattr(self.instance, "review_period", None)
        qs = PerformanceReview.objects.filter(tenant_id=tenant_id, staff=staff, review_period=period)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A review already exists for this staff member and period.")
        return attrs


class OnboardingTaskSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingTask
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "completed_at", "completed_by"]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}" if obj.staff_id else ""
