"""
Staff CRUD (Course/Lesson/Enrollment viewsets) plus a public course
catalog — no login required to browse or enroll, same public posture
already established by storefront/blog/forum. Every public view here
resolves its own tenant from the `slug` URL segment rather than from
request.tenant_id, since there's no authenticated session to derive it
from. Mounted paths are exempted from the tenant/auth middleware — see
core/middleware/tenant.py.
"""

from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from platform.tenant.models import Tenant
from products.cycom.elearning.models import Course, Enrollment, Lesson, LessonProgress
from products.cycom.elearning.serializers import (
    CourseSerializer,
    EnrollmentSerializer,
    LessonSerializer,
    PublicCourseDetailSerializer,
    PublicCourseListSerializer,
    PublicEnrollSerializer,
    PublicLessonDetailSerializer,
)


class CourseViewSet(TenantScopedModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filterset_fields = ["is_published"]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        course = self.get_object()
        course.is_published = True
        course.save(update_fields=["is_published", "updated_at"])
        return Response(CourseSerializer(course).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        course = self.get_object()
        course.is_published = False
        course.save(update_fields=["is_published", "updated_at"])
        return Response(CourseSerializer(course).data)


class LessonViewSet(TenantScopedModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filterset_fields = ["course"]


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff reporting only — enrollments are created by guests via the
    public API, never authored directly by staff."""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticatedViaClaims]
    filterset_fields = ["course"]

    def get_queryset(self):
        qs = Enrollment.objects.annotate(completed_lesson_count=Count("progress")).order_by("-created_at")
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is None:
            return qs
        return qs.filter(tenant_id=tenant_id)


def _get_tenant(slug):
    try:
        return Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist:
        raise ValidationError("Course catalog not found.")


def _get_published_course_or_404(tenant_id, course_slug):
    try:
        return Course.objects.get(tenant_id=tenant_id, slug=course_slug, is_published=True)
    except Course.DoesNotExist:
        raise ValidationError("Course not found.")


def _get_enrollment_or_404(course, token):
    try:
        return Enrollment.objects.get(course=course, token=token)
    except Enrollment.DoesNotExist:
        raise ValidationError("Enrollment not found.")


@api_view(["GET"])
@permission_classes([AllowAny])
def public_course_list(request, slug):
    tenant = _get_tenant(slug)
    courses = Course.objects.filter(tenant_id=tenant.id, is_published=True).annotate(lesson_count=Count("lessons"))
    return Response(PublicCourseListSerializer(courses, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_course_detail(request, slug, course_slug):
    tenant = _get_tenant(slug)
    course = _get_published_course_or_404(tenant.id, course_slug)
    return Response(PublicCourseDetailSerializer(course).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def public_enroll(request, slug, course_slug):
    tenant = _get_tenant(slug)
    course = _get_published_course_or_404(tenant.id, course_slug)
    serializer = PublicEnrollSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    enrollment = serializer.save(tenant_id=tenant.id, course=course)
    return Response({"token": enrollment.token}, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_lesson_detail(request, slug, course_slug, lesson_slug):
    tenant = _get_tenant(slug)
    course = _get_published_course_or_404(tenant.id, course_slug)
    try:
        lesson = Lesson.objects.get(course=course, slug=lesson_slug)
    except Lesson.DoesNotExist:
        raise ValidationError("Lesson not found.")
    return Response(PublicLessonDetailSerializer(lesson).data)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def public_lesson_progress(request, slug, course_slug, lesson_slug):
    """GET checks completion for `?token=<enrollment token>`; POST with
    `{"token": ...}` in the body marks it complete (idempotent)."""
    tenant = _get_tenant(slug)
    course = _get_published_course_or_404(tenant.id, course_slug)
    try:
        lesson = Lesson.objects.get(course=course, slug=lesson_slug)
    except Lesson.DoesNotExist:
        raise ValidationError("Lesson not found.")

    token = request.data.get("token") if request.method == "POST" else request.query_params.get("token")
    if not token:
        raise ValidationError("token is required.")
    enrollment = _get_enrollment_or_404(course, token)

    if request.method == "POST":
        LessonProgress.objects.get_or_create(tenant_id=tenant.id, enrollment=enrollment, lesson=lesson)
        completed = True
    else:
        completed = LessonProgress.objects.filter(enrollment=enrollment, lesson=lesson).exists()

    total = course.lessons.count()
    done = LessonProgress.objects.filter(enrollment=enrollment, lesson__course=course).count()
    return Response(
        {
            "completed": completed,
            "progress_percent": round(done / total * 100) if total else 0,
        }
    )
