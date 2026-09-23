from rest_framework import serializers

from products.cycom.elearning.models import Course, Enrollment, Lesson, LessonProgress


class CourseSerializer(serializers.ModelSerializer):
    """Staff CRUD — full fields."""

    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "slug", "created_at", "updated_at"]


class LessonSerializer(serializers.ModelSerializer):
    """Staff CRUD — full fields."""

    class Meta:
        model = Lesson
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "slug", "created_at", "updated_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    """Staff — read-only reporting on who's enrolled and how far they got."""

    completed_lesson_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "tenant_id", "course", "token", "student_name", "student_email", "completed_lesson_count", "created_at"]
        read_only_fields = fields


class PublicLessonSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "slug", "order"]


class PublicCourseListSerializer(serializers.ModelSerializer):
    lesson_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "slug", "description", "lesson_count", "created_at"]


class PublicCourseDetailSerializer(serializers.ModelSerializer):
    lessons = PublicLessonSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "slug", "description", "lessons", "created_at"]


class PublicLessonDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "slug", "content", "order"]


class PublicEnrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["student_name", "student_email"]
