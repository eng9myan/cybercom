from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from platform.api.permissions import _roles, actor

from .models import EphemeralEnvironment
from .serializers import EphemeralEnvironmentSerializer
from .tasks import destroy_environment_task, provision_environment_task


class IsPlatformAdmin(BasePermission):
    """Strictly platform_admin -- this view triggers real cloud spend
    (an OCI compute instance per environment), a tighter gate than the
    generic IsApiAdmin (platform_admin or api_admin) used elsewhere.
    Reuses platform.api.permissions' own role-extraction logic rather
    than re-deriving it (that module's other permission classes are the
    only other callers today, but the claims/session fallback shape is
    exactly the same here)."""

    def has_permission(self, request, view) -> bool:
        return "platform_admin" in _roles(request)


class EphemeralEnvironmentViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """POST creates the row and enqueues provisioning asynchronously --
    the request returns immediately with status="queued"; poll GET for
    status/public_ip. DELETE-equivalent is the explicit `destroy` action,
    not the DRF default destroy, so a plain mis-click DELETE can't tear
    down a real instance without hitting the dedicated action."""

    queryset = EphemeralEnvironment.objects.all()
    serializer_class = EphemeralEnvironmentSerializer
    permission_classes = [IsPlatformAdmin]
    filterset_fields = ["app", "status"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        env = serializer.save(requested_by=actor(request))
        provision_environment_task.delay(str(env.id))
        # Under CELERY_TASK_ALWAYS_EAGER (tests) the task above has already
        # run synchronously by the time .delay() returns, so `env`'s
        # in-memory state is stale the same way a prefetch-cached instance
        # would be — re-fetch rather than serialize the object we already
        # hold, or the response would show "queued" after it's actually
        # already "ready"/"failed".
        env.refresh_from_db()
        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(env).data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"])
    def destroy_environment(self, request, pk=None):
        env = self.get_object()
        if env.status in ("destroying", "destroyed"):
            return Response({"detail": f"Already {env.status}."}, status=status.HTTP_400_BAD_REQUEST)
        destroy_environment_task.delay(str(env.id))
        env.refresh_from_db()  # same staleness note as create() above
        return Response(self.get_serializer(env).data)
