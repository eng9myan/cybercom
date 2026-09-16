from rest_framework import serializers

from products.cyed.gradebook.models import (
    Assessment,
    Grade,
    Rubric,
    RubricCriterion,
    RubricLevel,
    RubricMark,
)


class RubricLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RubricLevel
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate_descriptor(self, value):
        # A level called "Good" with no description is a number in disguise,
        # and two teachers will not agree on what it means.
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Describe what work at this level looks like — a label alone is not a "
                "standard anyone can mark against consistently."
            )
        return value


class RubricCriterionSerializer(serializers.ModelSerializer):
    levels = RubricLevelSerializer(many=True, read_only=True)

    class Meta:
        model = RubricCriterion
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RubricSerializer(serializers.ModelSerializer):
    criteria = RubricCriterionSerializer(many=True, read_only=True)
    total_marks = serializers.SerializerMethodField()

    class Meta:
        model = Rubric
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_total_marks(self, obj) -> str:
        return str(obj.total_marks())


class RubricMarkSerializer(serializers.ModelSerializer):
    criterion_name = serializers.CharField(source="criterion.name", read_only=True)
    level_label = serializers.CharField(source="level.label", read_only=True)
    descriptor = serializers.CharField(source="level.descriptor", read_only=True)

    class Meta:
        model = RubricMark
        fields = "__all__"
        # Marks are written through the assessment's rubric-marking action, so
        # the derived score cannot drift from the criteria behind it.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at", "grade", "criterion", "level",
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")
    rubric_name = serializers.CharField(source="rubric.name", read_only=True, default="")

    class Meta:
        model = Assessment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class GradeSerializer(serializers.ModelSerializer):
    percentage = serializers.ReadOnlyField()
    student_name = serializers.SerializerMethodField()
    rubric_marks = RubricMarkSerializer(many=True, read_only=True)

    class Meta:
        model = Grade
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip()
