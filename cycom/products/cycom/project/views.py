from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.project.models import Project, Task, TimesheetEntry
from products.cycom.project.scheduling import DependencyCycle, compute_schedule
from products.cycom.project.serializers import (
    ProjectSerializer,
    TaskSerializer,
    TimesheetEntrySerializer,
)


class ProjectViewSet(TenantScopedModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        """Critical-path schedule for this project's tasks: early/late start
        and finish, slack, and which tasks are on the critical path."""
        project = self.get_object()
        tasks = (
            Task.objects.filter(tenant_id=request.tenant_id, project=project)
            .prefetch_related("depends_on")
        )
        try:
            return Response(compute_schedule(tasks))
        except DependencyCycle as exc:
            return Response(
                {"detail": str(exc), "cycle_task_ids": [str(t) for t in exc.task_ids]},
                status=409,
            )


class TaskViewSet(TenantScopedModelViewSet):
    queryset = Task.objects.select_related("project").prefetch_related("depends_on").all()
    serializer_class = TaskSerializer
    filterset_fields = ["project", "stage", "assignee"]


class TimesheetEntryViewSet(TenantScopedModelViewSet):
    # Bare-array response — the frontend's account.analytic.line adapter
    # (cycomServer.ts) reads a plain list, same reasoning as esign.
    pagination_class = None
    queryset = TimesheetEntry.objects.select_related("task").all()
    serializer_class = TimesheetEntrySerializer
