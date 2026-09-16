from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsPastoralOrLeadership, has_ai_consent
from products.cyed.ai_agents import integrity, socratic, teacher_tools, tutor
from products.cyed.ai_agents.models import (
    AgentDefinition,
    AgentInteractionLog,
    GeneratedArtifact,
    IntegrityReview,
)
from products.cyed.ai_agents.serializers import (
    AgentDefinitionSerializer,
    AgentInteractionLogSerializer,
    GeneratedArtifactSerializer,
    IntegrityReviewSerializer,
)


class AgentDefinitionViewSet(TenantScopedModelViewSet):
    queryset = AgentDefinition.objects.all()
    serializer_class = AgentDefinitionSerializer


class AgentInteractionLogViewSet(TenantScopedModelViewSet):
    queryset = AgentInteractionLog.objects.select_related("agent").all()
    serializer_class = AgentInteractionLogSerializer


def _actor(request):
    return request.user_session.get("email", "") if hasattr(request, "user_session") else ""


def _require_tenant(request):
    tenant_id = getattr(request, "tenant_id", None)
    return tenant_id


class TutorAskView(APIView):
    """
    POST /api/v1/ai/tutor/ask/
    Body: { question, student?, year_level?, learning_area? }
    Curriculum-grounded, cited answer; declines out-of-curriculum questions;
    adapts to the student's LearnerProfile when given.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def post(self, request):
        tenant_id = _require_tenant(request)
        if tenant_id is None:
            return Response({"detail": "A tenant context is required."}, status=status.HTTP_400_BAD_REQUEST)
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"detail": "question is required."}, status=status.HTTP_400_BAD_REQUEST)
        student = request.data.get("student")
        if student and not has_ai_consent(tenant_id, student):
            return Response(
                {"detail": "Generative-AI consent is not recorded for this student."},
                status=status.HTTP_403_FORBIDDEN,
            )
        year_level = request.data.get("year_level")
        result = tutor.ask(
            tenant_id=tenant_id,
            question=question,
            student_id=student,
            year_level=int(year_level) if year_level not in (None, "") else None,
            learning_area=request.data.get("learning_area"),
            actor=_actor(request),
        )
        return Response(result, status=status.HTTP_200_OK)


class SocraticAskView(APIView):
    """
    POST /api/v1/ai/tutor/socratic/
    Body: { question, student?, year_level?, learning_area? }
    Student AI in Socratic mode — returns guiding questions/hints only, never
    the answer. Grounded in the curriculum; student input is anonymised.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def post(self, request):
        tenant_id = _require_tenant(request)
        if tenant_id is None:
            return Response({"detail": "A tenant context is required."}, status=status.HTTP_400_BAD_REQUEST)
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"detail": "question is required."}, status=status.HTTP_400_BAD_REQUEST)
        student = request.data.get("student")
        if student and not has_ai_consent(tenant_id, student):
            return Response(
                {"detail": "Generative-AI consent is not recorded for this student."},
                status=status.HTTP_403_FORBIDDEN,
            )
        year_level = request.data.get("year_level")
        result = socratic.ask(
            tenant_id=tenant_id,
            question=question,
            student_id=student,
            year_level=int(year_level) if year_level not in (None, "") else None,
            learning_area=request.data.get("learning_area"),
            actor=_actor(request),
        )
        return Response(result, status=status.HTTP_200_OK)


class _GenerateView(APIView):
    """Shared base for the teacher-tool generators (each returns a pending artifact)."""

    permission_classes = [IsAuthenticatedViaClaims]

    def _run(self, request, fn, **kwargs):
        tenant_id = _require_tenant(request)
        if tenant_id is None:
            return Response({"detail": "A tenant context is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            artifact = fn(tenant_id=tenant_id, generated_by=_actor(request), **kwargs)
        except teacher_tools.NoGroundingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except teacher_tools.AgentNotProvisioned as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = GeneratedArtifactSerializer(artifact).data
        return Response(data, status=status.HTTP_201_CREATED)


class LessonPlannerGenerateView(_GenerateView):
    """POST /api/v1/ai/lesson-planner/generate/  Body: { topic, year_level?, learning_area?, subject? }"""

    def post(self, request):
        topic = (request.data.get("topic") or "").strip()
        if not topic:
            return Response({"detail": "topic is required."}, status=status.HTTP_400_BAD_REQUEST)
        yl = request.data.get("year_level")
        return self._run(
            request, teacher_tools.generate_lesson_plan, topic=topic,
            year_level=int(yl) if yl not in (None, "") else None,
            learning_area=request.data.get("learning_area"),
            subject=request.data.get("subject", ""),
        )


class RubricGenerateView(_GenerateView):
    """POST /api/v1/ai/rubric/generate/  Body: { assessment_title, year_level?, learning_area? }"""

    def post(self, request):
        title = (request.data.get("assessment_title") or "").strip()
        if not title:
            return Response({"detail": "assessment_title is required."}, status=status.HTTP_400_BAD_REQUEST)
        yl = request.data.get("year_level")
        return self._run(
            request, teacher_tools.generate_rubric, assessment_title=title,
            year_level=int(yl) if yl not in (None, "") else None,
            learning_area=request.data.get("learning_area"),
        )


class DifferentiatorGenerateView(_GenerateView):
    """POST /api/v1/ai/differentiator/generate/  Body: { topic, year_level?, learning_area?, student? }"""

    def post(self, request):
        topic = (request.data.get("topic") or "").strip()
        if not topic:
            return Response({"detail": "topic is required."}, status=status.HTTP_400_BAD_REQUEST)
        yl = request.data.get("year_level")
        return self._run(
            request, teacher_tools.generate_differentiated_task, topic=topic,
            year_level=int(yl) if yl not in (None, "") else None,
            learning_area=request.data.get("learning_area"),
            student_id=request.data.get("student"),
        )


class GeneratedArtifactViewSet(TenantScopedModelViewSet):
    """The human-in-the-loop queue: teachers review, then approve/reject."""

    queryset = GeneratedArtifact.objects.select_related("agent").all()
    serializer_class = GeneratedArtifactSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]  # no PUT/PATCH; use actions

    def create(self, request, *args, **kwargs):
        # Artifacts must come from the grounded generator endpoints, never a
        # direct POST (which would bypass curriculum grounding + HITL setup).
        return Response(
            {"detail": "Create artifacts via /ai/lesson-planner|rubric|differentiator/generate/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        artifact_type = params.get("artifact_type")
        status_filter = params.get("status")
        if artifact_type:
            qs = qs.filter(artifact_type=artifact_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        artifact = self.get_object()
        artifact.approve(reviewer=_actor(request), note=request.data.get("note", ""))
        return Response(self.get_serializer(artifact).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        artifact = self.get_object()
        artifact.reject(reviewer=_actor(request), note=request.data.get("note", ""))
        return Response(self.get_serializer(artifact).data)


class IntegrityReviewViewSet(TenantScopedModelViewSet):
    """
    Create a review from process-provenance evidence (server computes the advisory
    risk band); a human then records the authoritative decision via `decide`.
    Restricted to pastoral/leadership — integrity flags are sensitive.
    """

    permission_classes = [IsPastoralOrLeadership]

    queryset = IntegrityReview.objects.select_related("student").all()
    serializer_class = IntegrityReviewSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        student = params.get("student")
        decision = params.get("decision")
        risk_band = params.get("risk_band")
        if student:
            qs = qs.filter(student_id=student)
        if decision:
            qs = qs.filter(decision=decision)
        if risk_band:
            qs = qs.filter(risk_band=risk_band)
        return qs

    def perform_create(self, serializer):
        evidence = {
            "draft_versions": serializer.validated_data.get("draft_versions", 0),
            "edit_span_minutes": serializer.validated_data.get("edit_span_minutes", 0),
            "paste_events": serializer.validated_data.get("paste_events", 0),
            "large_paste_events": serializer.validated_data.get("large_paste_events", 0),
            "disclosed_ai_use": serializer.validated_data.get("disclosed_ai_use", False),
        }
        band, signals = integrity.assess(evidence)
        serializer.save(tenant_id=self.request.tenant_id, risk_band=band, signals=signals, decision="pending")

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        review = self.get_object()
        decision = request.data.get("decision")
        valid = {c[0] for c in IntegrityReview.DECISION_CHOICES}
        if decision not in valid:
            return Response(
                {"detail": f"decision must be one of {sorted(valid)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        review.decide(decision, decided_by=_actor(request), note=request.data.get("note", ""))
        return Response(self.get_serializer(review).data)
