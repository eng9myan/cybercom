from core.viewsets import TenantScopedModelViewSet
from products.cycom.project.models import Project, Task, TimesheetEntry
from products.cycom.project.serializers import (
    ProjectSerializer,
    TaskSerializer,
    TimesheetEntrySerializer,
)


class ProjectViewSet(TenantScopedModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(TenantScopedModelViewSet):
    queryset = Task.objects.select_related("project").all()
    serializer_class = TaskSerializer


class TimesheetEntryViewSet(TenantScopedModelViewSet):
    # Bare-array response — the frontend's account.analytic.line adapter
    # (cycomServer.ts) reads a plain list, same reasoning as esign.
    pagination_class = None
    queryset = TimesheetEntry.objects.select_related("task").all()
    serializer_class = TimesheetEntrySerializer
