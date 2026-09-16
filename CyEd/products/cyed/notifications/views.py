from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, is_staff, visible_student_ids
from products.cyed.notifications.models import Notification
from products.cyed.notifications.serializers import NotificationSerializer
from products.cyed.notifications.services import send_announcement


class NotificationViewSet(TenantScopedModelViewSet):
    """
    Inbox: staff see all; guardians/students see notifications for their own
    children/self or addressed to their email. Announcements are staff-only.
    """

    queryset = Notification.objects.select_related("student").all()
    serializer_class = NotificationSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "mark_read"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        if is_staff(self.request):
            return self._filter(qs)
        visible = visible_student_ids(self.request, self.request.tenant_id)
        email = (getattr(self.request, "user_session", {}) or {}).get("email", "")
        qs = qs.filter(Q(student_id__in=visible or []) | Q(recipient_email__iexact=email))
        return self._filter(qs)

    def _filter(self, qs):
        params = self.request.query_params
        category = params.get("category")
        status_f = params.get("status")
        student = params.get("student")
        if category:
            qs = qs.filter(category=category)
        if status_f:
            qs = qs.filter(status=status_f)
        if student:
            qs = qs.filter(student_id=student)
        return qs

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Use /notifications/announce/ to send messages."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.status = "read"
        n.read_at = timezone.now()
        n.save(update_fields=["status", "read_at", "updated_at"])
        return Response(self.get_serializer(n).data)

    @action(detail=False, methods=["post"])
    def announce(self, request):
        """Staff broadcast to a student's guardians (student id) or all guardians."""
        subject = (request.data.get("subject") or "").strip()
        if not subject:
            return Response({"detail": "subject is required."}, status=status.HTTP_400_BAD_REQUEST)
        student = None
        student_id = request.data.get("student")
        if student_id:
            from products.cyed.sis.models import Student
            student = Student.objects.filter(tenant_id=request.tenant_id, id=student_id).first()
        created = send_announcement(
            request.tenant_id,
            subject=subject,
            body=request.data.get("body", ""),
            student=student,
            category=request.data.get("category", "announcement"),
            channel=request.data.get("channel", "in_app"),
        )
        return Response({"created": len(created)}, status=status.HTTP_201_CREATED)
