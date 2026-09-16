from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.gradebook import services
from products.cyed.gradebook.models import (
    Assessment,
    Grade,
    Rubric,
    RubricCriterion,
    RubricLevel,
)
from products.cyed.gradebook.serializers import (
    AssessmentSerializer,
    GradeSerializer,
    RubricCriterionSerializer,
    RubricLevelSerializer,
    RubricSerializer,
)
from products.cyed.governance.access import AuditedTenantViewSet, scope_queryset_by_student


class AssessmentViewSet(TenantScopedModelViewSet):
    queryset = Assessment.objects.select_related("class_section").all()
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        class_section = self.request.query_params.get("class_section")
        if class_section:
            qs = qs.filter(class_section_id=class_section)
        return qs

    @action(detail=True, methods=["post"], url_path="bulk-grade")
    def bulk_grade(self, request, pk=None):
        """
        Enter a whole assessment's marks in one request.

        Body: ``{"grades": [{"student": "<uuid>", "score": 17, "comment": "",
        "achievement_level": "B"}, ...]}``

        The batch is validated as a whole and written all-or-nothing: a score
        above the assessment maximum, an unknown achievement level, or a
        student who is not in the class rejects the entire submission. A
        half-applied batch would leave a teacher unable to tell which marks
        landed.

        Re-submitting updates existing marks rather than failing.
        """
        assessment = self.get_object()
        try:
            summary = services.bulk_enter_grades(
                assessment=assessment,
                rows=request.data.get("grades"),
                tenant_id=request.tenant_id,
            )
        except services.GradeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(summary)

    @action(detail=True, methods=["post"], url_path="rubric-mark")
    def rubric_mark(self, request, pk=None):
        """
        Mark one student against this assessment's rubric.

        Body: ``{"student": uuid, "selections": {"<criterion>": "<level>"},
        "comment": "..."}``

        The score is derived from the selections — there is no way to type a
        total that disagrees with the criteria behind it.
        """
        assessment = self.get_object()
        student_id = request.data.get("student")
        if not student_id:
            return Response({"detail": "student is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            result = services.mark_against_rubric(
                assessment=assessment,
                student_id=student_id,
                selections=request.data.get("selections") or {},
                comment=request.data.get("comment", ""),
                tenant_id=request.tenant_id,
            )
        except services.RubricError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)

    @action(detail=True, methods=["get"], url_path="mark-sheet")
    def mark_sheet(self, request, pk=None):
        """The class list with current marks — what a marking screen loads."""
        assessment = self.get_object()
        grades = {
            str(g.student_id): g
            for g in Grade.objects.select_related("student").filter(
                tenant_id=request.tenant_id, assessment=assessment
            )
        }
        rows = []
        for student_id in services.roster_student_ids(assessment.class_section_id, request.tenant_id):
            grade = grades.get(str(student_id))
            rows.append({
                "student": str(student_id),
                "name": f"{grade.student.first_name} {grade.student.last_name}".strip() if grade else None,
                "score": str(grade.score) if grade and grade.score is not None else None,
                "achievement_level": grade.achievement_level if grade else "",
                "comment": grade.comment if grade else "",
                "graded": bool(grade and grade.score is not None),
            })
        return Response({
            "assessment": str(assessment.id),
            "name": assessment.name,
            "max_score": str(assessment.max_score),
            "count": len(rows),
            "graded": sum(1 for r in rows if r["graded"]),
            "students": rows,
        })


class RubricViewSet(TenantScopedModelViewSet):
    """
    Reusable marking rubrics.

    Readable by any staff member — a teacher needs to see the standard they are
    marking against, and students are shown their own breakdown through their
    grade.
    """

    queryset = Rubric.objects.prefetch_related("criteria__levels").all()
    serializer_class = RubricSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("subject"):
            qs = qs.filter(subject__icontains=params["subject"])
        if params.get("year_level"):
            qs = qs.filter(year_level=params["year_level"])
        if params.get("active") == "1":
            qs = qs.filter(is_active=True)
        return qs


class RubricCriterionViewSet(TenantScopedModelViewSet):
    queryset = RubricCriterion.objects.prefetch_related("levels").all()
    serializer_class = RubricCriterionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("rubric"):
            qs = qs.filter(rubric_id=self.request.query_params["rubric"])
        return qs


class RubricLevelViewSet(TenantScopedModelViewSet):
    queryset = RubricLevel.objects.select_related("criterion").all()
    serializer_class = RubricLevelSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("criterion"):
            qs = qs.filter(criterion_id=self.request.query_params["criterion"])
        return qs


class GradeViewSet(AuditedTenantViewSet):
    """Marks are PII: parents/students see only their own; changes are audited."""

    queryset = Grade.objects.select_related("assessment", "student").all()
    serializer_class = GradeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        assessment = self.request.query_params.get("assessment")
        student = self.request.query_params.get("student")
        if assessment:
            qs = qs.filter(assessment_id=assessment)
        if student:
            qs = qs.filter(student_id=student)
        return qs
