"""
Staff-side (ChatSessionViewSet, reply/close moderation) plus a public chat
widget backend — polling, not websockets (no real-time transport exists
anywhere in cycom yet; user chose polling for v1 rather than adding
Channels/Redis as new infra). Every public view here resolves its own
tenant from the `slug` URL segment rather than from request.tenant_id,
since there's no authenticated session to derive it from — same pattern
as esign/storefront/blog/forum. Mounted paths are exempted from the
tenant/auth middleware — see core/middleware/tenant.py.
"""

from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.throttling import PublicWriteRateThrottle
from core.viewsets import TenantScopedModelViewSet
from platform.tenant.models import Tenant
from products.cycom.livechat.models import ChatMessage, ChatSession
from products.cycom.livechat.serializers import (
    ChatMessageSerializer,
    ChatSessionSerializer,
    PublicChatMessageSerializer,
    PublicChatSessionSerializer,
    PublicMessageCreateSerializer,
)


class ChatSessionViewSet(TenantScopedModelViewSet):
    """Authenticated staff — agent side of the widget."""

    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        session = self.get_object()
        if session.status == "closed":
            raise ValidationError("This chat session is closed.")
        body = (request.data.get("body") or "").strip()
        if not body:
            raise ValidationError("body is required.")
        message = ChatMessage.objects.create(
            tenant_id=session.tenant_id, session=session, sender="agent", body=body
        )
        return Response(ChatMessageSerializer(message).data, status=201)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        session = self.get_object()
        session.status = "closed"
        session.save(update_fields=["status", "updated_at"])
        return Response(ChatSessionSerializer(session).data)


def _get_tenant(slug):
    try:
        return Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist:
        raise ValidationError("Chat not found.")


def _get_session_or_404(tenant_id, token):
    try:
        return ChatSession.objects.get(tenant_id=tenant_id, token=token)
    except ChatSession.DoesNotExist:
        raise ValidationError("Chat session not found.")


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def public_session_create(request, slug):
    tenant = _get_tenant(slug)
    session = ChatSession.objects.create(
        tenant_id=tenant.id,
        visitor_name=request.data.get("visitor_name", ""),
        visitor_email=request.data.get("visitor_email", ""),
    )
    return Response(PublicChatSessionSerializer(session).data, status=201)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def public_messages(request, slug, token):
    """GET polls for messages (optionally `?since=<ISO timestamp>` to fetch
    only what's new); POST sends a visitor message. One URL, one session
    lookup — mirrors how a chat widget actually uses this endpoint."""
    tenant = _get_tenant(slug)
    session = _get_session_or_404(tenant.id, token)

    if request.method == "POST":
        if session.status == "closed":
            raise ValidationError("This chat session is closed.")
        serializer = PublicMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(tenant_id=tenant.id, session=session, sender="visitor")
        return Response(PublicChatMessageSerializer(message).data, status=201)

    messages = session.messages.all()
    since = request.query_params.get("since")
    if since:
        messages = messages.filter(created_at__gt=since)
    return Response(
        {
            "status": session.status,
            "messages": PublicChatMessageSerializer(messages, many=True).data,
        }
    )
