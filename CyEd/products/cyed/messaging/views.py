from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import ADMIN, LEADERSHIP, _email, has_any, is_staff
from products.cyed.messaging import services
from products.cyed.messaging.models import Message, MessageThread
from products.cyed.messaging.serializers import MessageSerializer, MessageThreadSerializer


class MessageThreadViewSet(TenantScopedModelViewSet):
    """
    Conversations between school and home.

    Readable only by participants — plus pastoral staff and leadership for any
    thread involving a student, because adult↔child conversation has to be
    observable. Threads are created through `open/` and messages through
    `reply/`, so membership and safeguarding rules cannot be bypassed by
    posting a bare row.
    """

    queryset = MessageThread.objects.select_related("student").prefetch_related(
        "participants", "messages"
    ).all()
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticatedViaClaims]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return services.visible_threads(self.request, super().get_queryset())

    def create(self, request, *args, **kwargs):
        """
        Closed off deliberately.

        `http_method_names` has to allow POST for `open/` and `reply/`, and
        that also exposes the router's default create route. Creating a thread
        that way would skip participant resolution and the safeguarding rules
        entirely — leaving a readable-by-nobody thread at best, and an
        unobserved adult↔child channel at worst.
        """
        return Response(
            {"detail": "Start a conversation through /threads/open/ so participants are set."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["get"])
    def inbox(self, request):
        """Threads with unread counts, most recently active first."""
        rows = services.inbox(request, super().get_queryset())
        return Response({"count": len(rows), "results": rows})

    @action(detail=False, methods=["post"])
    def open(self, request):
        """
        Start a conversation and post its first message.

        Body: ``{"subject": "...", "body": "...", "kind": "teacher_parent",
        "student": "<uuid>", "staff": [uuid], "guardians": [uuid],
        "students": [uuid]}``

        A guardian may only open a thread about a child they can already see.
        """
        try:
            thread = services.open_thread(
                request,
                subject=request.data.get("subject", ""),
                body=request.data.get("body", ""),
                kind=request.data.get("kind", "teacher_parent"),
                student_id=request.data.get("student"),
                staff_ids=request.data.get("staff") or [],
                guardian_ids=request.data.get("guardians") or [],
                student_ids=request.data.get("students") or [],
            )
        except services.MessagingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(thread).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        """Append a message to this conversation."""
        thread = self.get_object()
        try:
            message = services.post_message(request, thread, request.data.get("body", ""))
        except services.MessagingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        thread = self.get_object()
        participant = services.mark_read(thread, request)
        if participant is None:
            return Response(
                {"detail": "You are observing this conversation, not participating in it."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"thread": str(thread.id), "last_read_at": participant.last_read_at})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        Close a conversation. Staff only — a family cannot end a thread the
        school still needs an answer in, and the record is preserved either way.
        """
        if not is_staff(request):
            return Response({"detail": "Only staff may close a conversation."},
                            status=status.HTTP_403_FORBIDDEN)
        thread = self.get_object()
        if thread.is_closed:
            return Response({"detail": "This conversation is already closed."},
                            status=status.HTTP_409_CONFLICT)
        thread.close(by_email=_email(request))
        return Response(self.get_serializer(thread).data)


class MessageViewSet(TenantScopedModelViewSet):
    """
    Read-only view of individual messages, scoped to threads the caller may see.

    Writing goes through `threads/{id}/reply/`; there is no edit or delete path
    because correspondence with families is a record, not a draft.
    """

    queryset = Message.objects.select_related("thread").all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticatedViaClaims]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        threads = services.visible_threads(
            self.request, MessageThread.objects.filter(tenant_id=self.request.tenant_id)
        )
        qs = qs.filter(thread__in=threads)
        if self.request.query_params.get("thread"):
            qs = qs.filter(thread_id=self.request.query_params["thread"])
        return qs
