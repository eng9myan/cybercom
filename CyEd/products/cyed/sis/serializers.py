from rest_framework import serializers

from products.cyed.sis.models import (
    AcademicYear,
    ClassSection,
    Enrolment,
    Family,
    Guardian,
    Student,
)


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class FamilySerializer(serializers.ModelSerializer):
    billing_email = serializers.CharField(read_only=True)
    postal_address = serializers.CharField(read_only=True)
    student_count = serializers.SerializerMethodField()
    enrolled_count = serializers.SerializerMethodField()
    siblings = serializers.SerializerMethodField()

    class Meta:
        model = Family
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_student_count(self, obj) -> int:
        return obj.students.count()

    def get_enrolled_count(self, obj) -> int:
        return obj.students_enrolled().count()

    def get_siblings(self, obj) -> list:
        """Children eldest-first with the ordinal the discount engine will use."""
        enrolled_ids = list(obj.students_enrolled().values_list("id", flat=True))
        rows = []
        for s in obj.students_ordered():
            ordinal = enrolled_ids.index(s.id) + 1 if s.id in enrolled_ids else None
            rows.append({
                "student": str(s.id),
                "name": f"{s.first_name} {s.last_name}".strip(),
                "year_level": s.year_level,
                "date_of_birth": s.date_of_birth,
                "enrolment_status": s.enrolment_status,
                "sibling_ordinal": ordinal,
            })
        return rows

    def validate_billing_contact(self, guardian):
        # A household cannot be billed through a guardian belonging to another
        # tenant — the tenant is injected on save, so check it here.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        if guardian is not None and tenant_id is not None and str(guardian.tenant_id) != str(tenant_id):
            raise serializers.ValidationError("Billing contact belongs to a different tenant.")
        return guardian


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_full_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class ClassSectionSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True, default="")
    teacher_display = serializers.SerializerMethodField()

    class Meta:
        model = ClassSection
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_teacher_display(self, obj) -> str:
        return obj.teacher_display()

    def validate_teacher(self, staff):
        """
        Refuse to put a teacher in front of a class without a current WWCC and
        teacher registration.

        Same rule as the timetable, enforced at the same moment: an expired
        clearance must stop classroom contact, not merely appear on a report.
        """
        if staff is None:
            return staff
        from products.cyed.hr.compliance import ComplianceError, assert_may_teach

        try:
            assert_may_teach(staff)
        except ComplianceError as exc:
            raise serializers.ValidationError(str(exc))
        return staff


class EnrolmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")

    class Meta:
        model = Enrolment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip()
