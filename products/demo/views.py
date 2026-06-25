from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DemoEnvironment, DemoTenant, DemoScenario, DemoSession, DemoResetRequest, ProductTour
from .serializers import (
    DemoEnvironmentSerializer, DemoTenantSerializer, DemoScenarioSerializer,
    DemoSessionSerializer, DemoResetRequestSerializer, ProductTourSerializer,
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


class DemoEnvironmentViewSet(BaseViewSet):
    queryset = DemoEnvironment.objects.all()
    serializer_class = DemoEnvironmentSerializer
    filterset_fields = ["demo_type", "status", "product_edition", "country_config"]
    search_fields = ["name", "code", "prospect_organization", "prospect_name"]
    ordering_fields = ["name", "status", "expires_at", "created_at"]

    @action(detail=True, methods=["post"])
    def reset(self, request, pk=None):
        env = self.get_object()
        requester = getattr(request.user, "id", None) or request.data.get("requested_by_id")
        if not requester:
            return Response({"detail": "requested_by_id is required."}, status=400)
        reset = DemoResetRequest.objects.create(
            tenant_id=env.tenant_id,
            environment=env,
            requested_by_id=requester,
            reason=request.data.get("reason", ""),
            status="pending",
        )
        env.status = "resetting"
        env.save(update_fields=["status", "updated_at"])
        return Response({"status": "reset_queued", "reset_request_id": str(reset.id)})

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        env = self.get_object()
        env.status = "paused"
        env.save(update_fields=["status", "updated_at"])
        return Response({"status": "paused"})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        env = self.get_object()
        env.status = "active"
        env.save(update_fields=["status", "updated_at"])
        return Response({"status": "active"})

    @action(detail=True, methods=["get"])
    def scenarios(self, request, pk=None):
        env = self.get_object()
        qs = env.scenarios.filter(is_active=True)
        return Response(DemoScenarioSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def sessions(self, request, pk=None):
        env = self.get_object()
        qs = env.sessions.all().order_by("-started_at")
        return Response(DemoSessionSerializer(qs, many=True).data)


class DemoTenantViewSet(BaseViewSet):
    queryset = DemoTenant.objects.select_related("environment")
    serializer_class = DemoTenantSerializer
    filterset_fields = ["environment", "tenant_type", "is_primary"]
    ordering_fields = ["tenant_name", "created_at"]


class DemoScenarioViewSet(BaseViewSet):
    queryset = DemoScenario.objects.select_related("environment")
    serializer_class = DemoScenarioSerializer
    filterset_fields = ["environment", "scenario_type", "is_interactive", "is_active", "ai_narration_enabled"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "estimated_duration_minutes", "created_at"]


class DemoSessionViewSet(BaseViewSet):
    queryset = DemoSession.objects.select_related("environment", "scenario")
    serializer_class = DemoSessionSerializer
    filterset_fields = ["environment", "scenario", "presenter_id"]
    ordering_fields = ["started_at", "feedback_score", "created_at"]

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        session = self.get_object()
        session.ended_at = timezone.now()
        session.feedback_score = request.data.get("feedback_score")
        session.feedback_notes = request.data.get("feedback_notes", "")
        session.follow_up_action = request.data.get("follow_up_action", "")
        session.save(update_fields=["ended_at", "feedback_score", "feedback_notes", "follow_up_action", "updated_at"])
        return Response({"status": "ended", "id": str(session.id)})


class DemoResetRequestViewSet(BaseViewSet):
    queryset = DemoResetRequest.objects.select_related("environment")
    serializer_class = DemoResetRequestSerializer
    filterset_fields = ["environment", "status", "requested_by_id"]
    ordering_fields = ["created_at"]


class ProductTourViewSet(BaseViewSet):
    queryset = ProductTour.objects.all()
    serializer_class = ProductTourSerializer
    filterset_fields = ["product_code", "language_code", "is_published"]
    search_fields = ["title", "subtitle"]
    ordering_fields = ["product_code", "view_count", "created_at"]

    @action(detail=True, methods=["post"])
    def record_view(self, request, pk=None):
        tour = self.get_object()
        tour.view_count += 1
        tour.save(update_fields=["view_count", "updated_at"])
        return Response({"status": "recorded", "view_count": tour.view_count})
