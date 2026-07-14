from rest_framework import serializers

from .models import (
    Certificate,
    Course,
    CourseModule,
    Enrollment,
    Exam,
    ExamAttempt,
    LearningPath,
)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CourseModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "enrolled_at", "created_at", "updated_at"]


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ExamAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempt
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "started_at", "created_at", "updated_at"]


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "issued_at", "created_at", "updated_at"]


class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
