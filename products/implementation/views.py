from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    ImplementationProject, ProjectMilestone, ProjectTask,
    CutoverChecklist, HypercareLog, MethodologyTemplate,
)
from .serializers import (
    ImplementationProjectSerializer, ProjectMilestoneSerializer, ProjectTaskSerializer,
    CutoverChecklistSerializer, HypercareLogSerializer, MethodologyTemplateSerializer,
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


class ImplementationProjectViewSet(BaseViewSet):
    queryset = ImplementationProject.objects.all()
    serializer_class = ImplementationProjectSerializer
    filterset_fields = ["methodology", "status", "customer_id", "assigned_pm_id"]
    search_fields = ["customer_name", "project_code", "phase"]
    ordering_fields = ["customer_name", "status", "start_date", "go_live_date", "created_at"]

    @action(detail=True, methods=["post"])
    def complete_phase(self, request, pk=None):
        project = self.get_object()
        phase_transitions = {
            "not_started": "discovery",
            "discovery": "design",
            "design": "build",
            "build": "test",
            "test": "cutover",
            "cutover": "go_live",
            "go_live": "hypercare",
            "hypercare": "closed",
        }
        next_status = phase_transitions.get(project.status)
        if next_status:
            project.status = next_status
            project.phase = next_status.replace("_", " ").title()
            project.save(update_fields=["status", "phase", "updated_at"])
        return Response({"status": project.status, "phase": project.phase, "id": str(project.id)})


class ProjectMilestoneViewSet(BaseViewSet):
    queryset = ProjectMilestone.objects.select_related("project")
    serializer_class = ProjectMilestoneSerializer
    filterset_fields = ["project", "status", "phase"]
    search_fields = ["milestone_name"]
    ordering_fields = ["target_date", "actual_date", "created_at"]


class ProjectTaskViewSet(BaseViewSet):
    queryset = ProjectTask.objects.select_related("project")
    serializer_class = ProjectTaskSerializer
    filterset_fields = ["project", "priority", "status", "task_category", "assigned_to_id"]
    search_fields = ["task_name"]
    ordering_fields = ["due_date", "priority", "created_at"]


class CutoverChecklistViewSet(BaseViewSet):
    queryset = CutoverChecklist.objects.select_related("project")
    serializer_class = CutoverChecklistSerializer
    filterset_fields = ["project", "checklist_type"]
    search_fields = ["checklist_name"]
    ordering_fields = ["created_at", "completed_at"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        checklist = self.get_object()
        checklist.completed_by_id = request.data.get("completed_by_id")
        checklist.completed_at = timezone.now()
        checklist.completed_items = checklist.items
        checklist.save(update_fields=["completed_by_id", "completed_at", "completed_items", "updated_at"])
        return Response({"completed_at": checklist.completed_at, "id": str(checklist.id)})


class HypercareLogViewSet(BaseViewSet):
    queryset = HypercareLog.objects.select_related("project")
    serializer_class = HypercareLogSerializer
    filterset_fields = ["project", "issue_type", "severity"]
    search_fields = ["description", "resolution"]
    ordering_fields = ["log_date", "severity", "created_at"]

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        log = self.get_object()
        log.resolved_by_id = request.data.get("resolved_by_id")
        log.resolved_at = timezone.now()
        log.resolution = request.data.get("resolution", log.resolution)
        log.save(update_fields=["resolved_by_id", "resolved_at", "resolution", "updated_at"])
        return Response({"resolved_at": log.resolved_at, "id": str(log.id)})


class MethodologyTemplateViewSet(BaseViewSet):
    queryset = MethodologyTemplate.objects.all()
    serializer_class = MethodologyTemplateSerializer
    filterset_fields = ["methodology", "is_active"]
    search_fields = ["name", "template_code", "description"]
    ordering_fields = ["name", "phase_count", "estimated_weeks", "created_at"]
