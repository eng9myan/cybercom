from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.todo.models import Task
from products.cycom.todo.serializers import TaskSerializer


class TaskViewSet(TenantScopedModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        task = self.get_object()
        task.is_done = True
        task.done_at = timezone.now()
        task.save(update_fields=["is_done", "done_at", "updated_at"])
        return Response(TaskSerializer(task).data)
