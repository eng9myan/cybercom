from core.viewsets import TenantScopedModelViewSet
from products.cycom.project.models import Project, Task
from products.cycom.project.serializers import ProjectSerializer, TaskSerializer


class ProjectViewSet(TenantScopedModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(TenantScopedModelViewSet):
    queryset = Task.objects.select_related("project").all()
    serializer_class = TaskSerializer
