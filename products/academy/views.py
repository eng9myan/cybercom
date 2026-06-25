from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    Course, CourseModule, Enrollment, Exam,
    ExamAttempt, Certificate, LearningPath,
)
from .serializers import (
    CourseSerializer, CourseModuleSerializer, EnrollmentSerializer, ExamSerializer,
    ExamAttemptSerializer, CertificateSerializer, LearningPathSerializer,
)


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request, "tenant_id", None))


class CourseViewSet(BaseViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filterset_fields = ["product_area", "target_audience", "level", "is_published", "language_code"]
    search_fields = ["title", "code", "description"]
    ordering_fields = ["title", "duration_hours", "level", "created_at"]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        course = self.get_object()
        course.is_published = True
        course.save(update_fields=["is_published", "updated_at"])
        return Response({"is_published": True, "id": str(course.id)})


class CourseModuleViewSet(BaseViewSet):
    queryset = CourseModule.objects.select_related("course")
    serializer_class = CourseModuleSerializer
    filterset_fields = ["course", "content_type", "is_required"]
    search_fields = ["title", "description"]
    ordering_fields = ["module_order", "duration_minutes", "created_at"]


class EnrollmentViewSet(BaseViewSet):
    queryset = Enrollment.objects.select_related("course")
    serializer_class = EnrollmentSerializer
    filterset_fields = ["course", "learner_id", "certificate_issued"]
    ordering_fields = ["enrolled_at", "completed_at", "progress_pct", "created_at"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        enrollment = self.get_object()
        enrollment.completed_at = timezone.now()
        enrollment.progress_pct = 100
        enrollment.save(update_fields=["completed_at", "progress_pct", "updated_at"])
        return Response({"completed_at": enrollment.completed_at, "id": str(enrollment.id)})

    @action(detail=True, methods=["post"])
    def update_progress(self, request, pk=None):
        enrollment = self.get_object()
        progress_pct = request.data.get("progress_pct")
        current_module_id = request.data.get("current_module_id")
        if progress_pct is not None:
            enrollment.progress_pct = progress_pct
        if current_module_id is not None:
            enrollment.current_module_id = current_module_id
        enrollment.save(update_fields=["progress_pct", "current_module_id", "updated_at"])
        return Response({"progress_pct": str(enrollment.progress_pct), "id": str(enrollment.id)})


class ExamViewSet(BaseViewSet):
    queryset = Exam.objects.select_related("course")
    serializer_class = ExamSerializer
    filterset_fields = ["course", "is_proctored"]
    search_fields = ["exam_title"]
    ordering_fields = ["pass_score_pct", "time_limit_minutes", "created_at"]


class ExamAttemptViewSet(BaseViewSet):
    queryset = ExamAttempt.objects.select_related("exam")
    serializer_class = ExamAttemptSerializer
    filterset_fields = ["exam", "learner_id", "passed"]
    ordering_fields = ["started_at", "submitted_at", "score_pct", "created_at"]

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        attempt = self.get_object()
        attempt.submitted_at = timezone.now()
        attempt.answers = request.data.get("answers", attempt.answers)
        score_pct = request.data.get("score_pct")
        if score_pct is not None:
            attempt.score_pct = score_pct
            attempt.passed = float(score_pct) >= attempt.exam.pass_score_pct
        attempt.save(update_fields=["submitted_at", "answers", "score_pct", "passed", "updated_at"])
        return Response({"submitted_at": attempt.submitted_at, "passed": attempt.passed, "id": str(attempt.id)})


class CertificateViewSet(BaseViewSet):
    queryset = Certificate.objects.select_related("course", "exam_attempt")
    serializer_class = CertificateSerializer
    filterset_fields = ["learner_id", "course", "certificate_type", "is_revoked"]
    search_fields = ["certificate_number"]
    ordering_fields = ["issued_at", "expires_at", "created_at"]

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        certificate = self.get_object()
        certificate.is_revoked = True
        certificate.save(update_fields=["is_revoked", "updated_at"])
        return Response({"is_revoked": True, "id": str(certificate.id)})


class LearningPathViewSet(BaseViewSet):
    queryset = LearningPath.objects.prefetch_related("courses")
    serializer_class = LearningPathSerializer
    filterset_fields = ["is_published", "target_role"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["name", "estimated_weeks", "created_at"]
