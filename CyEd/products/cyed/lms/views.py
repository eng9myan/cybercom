from core.viewsets import TenantScopedModelViewSet
from products.cyed.lms.models import Course, Lesson, Module
from products.cyed.lms.serializers import CourseSerializer, LessonSerializer, ModuleSerializer


class CourseViewSet(TenantScopedModelViewSet):
    queryset = Course.objects.prefetch_related("modules__lessons").all()
    serializer_class = CourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        subject = params.get("subject")
        year_level = params.get("year_level")
        if subject:
            qs = qs.filter(subject__iexact=subject)
        if year_level:
            qs = qs.filter(year_level=year_level)
        return qs


class ModuleViewSet(TenantScopedModelViewSet):
    queryset = Module.objects.select_related("course").prefetch_related("lessons").all()
    serializer_class = ModuleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        course = self.request.query_params.get("course")
        if course:
            qs = qs.filter(course_id=course)
        return qs


class LessonViewSet(TenantScopedModelViewSet):
    queryset = Lesson.objects.select_related("module").all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        module = params.get("module")
        curriculum_code = params.get("curriculum_code")
        if module:
            qs = qs.filter(module_id=module)
        if curriculum_code:
            qs = qs.filter(curriculum_code=curriculum_code)
        return qs
