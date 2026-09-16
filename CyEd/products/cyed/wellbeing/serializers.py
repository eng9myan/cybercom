from rest_framework import serializers

from products.cyed.wellbeing.models import (
    BehaviourIncident,
    LearnerProfile,
    SupportAdjustment,
    SupportGoal,
    SupportPlan,
    SupportPlanReview,
    WellbeingCheckIn,
    WellbeingNote,
)


class WellbeingCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellbeingCheckIn
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "sentiment_score", "sentiment_label", "flagged",
                            "created_at", "updated_at"]


class LearnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerProfile
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        # OneToOne on student — return a clean 400 rather than a DB IntegrityError.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None) if request else None
        student = attrs.get("student", getattr(self.instance, "student", None))
        if tenant_id and student is not None:
            qs = LearnerProfile.objects.filter(tenant_id=tenant_id, student=student)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"student": "This student already has a learner profile."})
        return attrs


class BehaviourIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviourIncident
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class WellbeingNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellbeingNote
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SupportAdjustmentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = SupportAdjustment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate_description(self, value):
        # "Provide support as needed" is what an auditor rejects and a relief
        # teacher cannot act on. A length floor is crude but catches the
        # placeholder text that gets typed when a form demands something.
        if len(value.strip()) < 15:
            raise serializers.ValidationError(
                "Describe what is actually done differently — concrete enough for a "
                "relief teacher to follow."
            )
        return value


class SupportGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportGoal
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SupportPlanReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportPlanReview
        fields = "__all__"
        # Reviews are recorded through the plan's action so the next review
        # date rolls forward with the meeting that set it.
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "recorded_by"]


class SupportPlanSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    adjustments = SupportAdjustmentSerializer(many=True, read_only=True)
    goals = SupportGoalSerializer(many=True, read_only=True)
    reviews = SupportPlanReviewSerializer(many=True, read_only=True)
    review_state = serializers.SerializerMethodField()
    nccd_level = serializers.SerializerMethodField()

    class Meta:
        model = SupportPlan
        fields = "__all__"
        # Status moves through activate/close so supersession happens and the
        # learner-profile flag stays in step.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "superseded_by", "closed_on", "closed_reason",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_review_state(self, obj) -> str:
        return obj.review_state()

    def get_nccd_level(self, obj) -> str:
        return obj.highest_adjustment()
