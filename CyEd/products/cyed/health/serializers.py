from rest_framework import serializers

from products.cyed.health.models import (
    ActionPlan,
    HealthRecord,
    ImmunisationDose,
    ImmunisationRecord,
    MedicalIncident,
    MedicationAdministration,
    MedicationAuthority,
    SickBayVisit,
)


class HealthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MedicalIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalIncident
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SickBayVisitSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    minutes_present = serializers.SerializerMethodField()

    class Meta:
        model = SickBayVisit
        fields = "__all__"
        # Closing is an action: it decides the outcome, records who collected
        # the child and sends the guardian alert. A PATCHable `outcome` would
        # let a visit be marked "sent home" with nobody told.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "departed_at", "outcome", "collected_by",
            "guardians_notified", "notified_at",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_is_open(self, obj) -> bool:
        return obj.is_open()

    def get_minutes_present(self, obj) -> int:
        return obj.minutes_present()


class ActionPlanSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    plan_type_display = serializers.CharField(source="get_plan_type_display", read_only=True)

    class Meta:
        model = ActionPlan
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_status(self, obj) -> str:
        return obj.status()

    def validate(self, attrs):
        steps = attrs.get("emergency_steps", getattr(self.instance, "emergency_steps", ""))
        if not (steps or "").strip():
            raise serializers.ValidationError({
                "emergency_steps": (
                    "A plan with no steps is not a plan. Record what a teacher should "
                    "actually do, in order."
                )
            })
        plan_type = attrs.get("plan_type", getattr(self.instance, "plan_type", ""))
        medication = attrs.get("medication", getattr(self.instance, "medication", ""))
        location = attrs.get(
            "medication_location", getattr(self.instance, "medication_location", "")
        )
        if plan_type in ActionPlan.CRITICAL_TYPES and medication and not location:
            raise serializers.ValidationError({
                "medication_location": (
                    "Say where the medication is kept. Knowing a child needs an EpiPen "
                    "without knowing where it is does not help in an emergency."
                )
            })
        return attrs


class ImmunisationDoseSerializer(serializers.ModelSerializer):
    disease_display = serializers.CharField(source="get_disease_display", read_only=True)

    class Meta:
        model = ImmunisationDose
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ImmunisationRecordSerializer(serializers.ModelSerializer):
    doses = ImmunisationDoseSerializer(many=True, read_only=True)
    acceptable_at_enrolment = serializers.SerializerMethodField()

    class Meta:
        model = ImmunisationRecord
        fields = "__all__"
        # `verified_by` is stamped from the authenticated user — a self-asserted
        # verifier proves nothing, exactly as with a staff clearance.
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "verified_by"]

    def get_acceptable_at_enrolment(self, obj) -> bool:
        return obj.is_acceptable_at_enrolment()

    def validate(self, attrs):
        status = attrs.get("status") or getattr(self.instance, "status", None)
        reason = attrs.get("exemption_reason") or getattr(self.instance, "exemption_reason", "")
        if status == "medical_exemption" and not reason:
            raise serializers.ValidationError({
                "exemption_reason": (
                    "Record the certified reason for a medical exemption — an "
                    "unexplained exemption cannot be defended to a public-health officer."
                )
            })
        return attrs


class MedicationAuthoritySerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = MedicationAuthority
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_is_current(self, obj) -> bool:
        return obj.is_current()

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "An authority cannot end before it begins."}
            )
        max_doses = attrs.get("max_doses_per_day", getattr(self.instance, "max_doses_per_day", 1))
        if max_doses == 0:
            raise serializers.ValidationError({
                "max_doses_per_day": (
                    "Use is_active=false to withdraw an authority. A ceiling of zero "
                    "would silently block every dose while still looking current."
                )
            })
        return attrs


class MedicationAdministrationSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    medication_name = serializers.CharField(source="authority.medication_name", read_only=True)
    administered_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicationAdministration
        fields = "__all__"
        # The whole record is written through the `administer` action so the
        # safety checks cannot be bypassed by posting a row directly.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at", "administered_on",
            "limit_override_by", "limit_override_reason",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_administered_by_name(self, obj) -> str:
        staff = obj.administered_by
        return f"{staff.first_name} {staff.last_name}".strip() if staff else ""
