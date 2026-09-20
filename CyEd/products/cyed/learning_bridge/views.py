from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    IsStaff,
    _email,
    is_staff,
    visible_student_ids,
)
from products.cyed.learning_bridge.models import FamilyResource, OfflineActivityPack
from products.cyed.learning_bridge.serializers import (
    FamilyResourceSerializer,
    OfflineActivityPackSerializer,
)
from products.cyed.learning_bridge.services import bridge_summary


class StaffWritesOnly(BasePermission):
    """Families read a published resource/pack; only staff curate them."""

    def has_permission(self, request, view) -> bool:
        if getattr(request, "auth_claims", None) is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_staff(request)


class FamilyResourceViewSet(TenantScopedModelViewSet):
    queryset = FamilyResource.objects.all()
    serializer_class = FamilyResourceSerializer
    permission_classes = [StaffWritesOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_staff(self.request):
            qs = qs.filter(is_published=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, created_by=_email(self.request))


class OfflineActivityPackViewSet(TenantScopedModelViewSet):
    queryset = OfflineActivityPack.objects.all()
    serializer_class = OfflineActivityPackSerializer
    permission_classes = [StaffWritesOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_staff(self.request):
            qs = qs.filter(is_published=True)
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def approve(self, request, pk=None):
        """Publish the pack, recording who signed off on it for families."""
        pack = self.get_object()
        pack.approved_by = _email(request)
        pack.is_published = True
        pack.save(update_fields=["approved_by", "is_published", "updated_at"])
        return Response(self.get_serializer(pack).data)


class LearningBridgeSummaryView(APIView):
    """
    ``GET /api/v1/learning-bridge/summary/?student=<uuid>``

    Staff must pass ``student``. A parent/student may omit it and gets their
    first visible child (or themselves) — the same "don't force a click to
    see anything" convenience the portal home page already uses elsewhere.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        from products.cyed.sis.models import Student

        visible = visible_student_ids(request, request.tenant_id)
        requested = request.query_params.get("student")

        if visible is None:  # staff
            if not requested:
                return Response(
                    {"detail": "Staff must pass ?student=<uuid>."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            student_id = requested
        else:
            if not visible:
                return Response(
                    {"detail": "No student is linked to this account."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if requested and requested not in {str(i) for i in visible}:
                return Response(
                    {"detail": "You may not view this student."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            student_id = requested or str(sorted(str(i) for i in visible)[0])

        student = Student.objects.filter(tenant_id=request.tenant_id, id=student_id).first()
        if student is None:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        summary = bridge_summary(request.tenant_id, student)
        summary["resources"] = FamilyResourceSerializer(summary["resources"], many=True).data
        summary["offline_packs"] = OfflineActivityPackSerializer(summary["offline_packs"], many=True).data
        return Response(summary)
