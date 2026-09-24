"""
Staff CRUD (ForumThreadViewSet/ForumReplyViewSet, moderation) plus a public
Q&A board — no login required to post, same public posture already
established by the storefront's guest checkout. Every public view here
resolves its own tenant from the `slug` URL segment rather than from
request.tenant_id, since there's no authenticated session to derive it
from. Mounted paths are exempted from the tenant/auth middleware the same
way esign/storefront/blog already are — see core/middleware/tenant.py.
"""

from django.db.models import Count
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.throttling import PublicWriteRateThrottle
from core.viewsets import TenantScopedModelViewSet
from platform.tenant.models import Tenant
from products.cycom.forum.models import ForumReply, ForumThread
from products.cycom.forum.serializers import (
    ForumReplySerializer,
    ForumThreadSerializer,
    PublicReplyCreateSerializer,
    PublicReplySerializer,
    PublicThreadCreateSerializer,
    PublicThreadDetailSerializer,
    PublicThreadListSerializer,
)


class ForumThreadViewSet(TenantScopedModelViewSet):
    """Authenticated staff moderation."""

    queryset = ForumThread.objects.all()
    serializer_class = ForumThreadSerializer
    filterset_fields = ["is_pinned", "is_locked"]

    @action(detail=True, methods=["post"])
    def pin(self, request, pk=None):
        thread = self.get_object()
        thread.is_pinned = True
        thread.save(update_fields=["is_pinned", "updated_at"])
        return Response(ForumThreadSerializer(thread).data)

    @action(detail=True, methods=["post"])
    def unpin(self, request, pk=None):
        thread = self.get_object()
        thread.is_pinned = False
        thread.save(update_fields=["is_pinned", "updated_at"])
        return Response(ForumThreadSerializer(thread).data)

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        thread = self.get_object()
        thread.is_locked = True
        thread.save(update_fields=["is_locked", "updated_at"])
        return Response(ForumThreadSerializer(thread).data)

    @action(detail=True, methods=["post"])
    def unlock(self, request, pk=None):
        thread = self.get_object()
        thread.is_locked = False
        thread.save(update_fields=["is_locked", "updated_at"])
        return Response(ForumThreadSerializer(thread).data)


class ForumReplyViewSet(TenantScopedModelViewSet):
    """Authenticated staff moderation."""

    queryset = ForumReply.objects.all()
    serializer_class = ForumReplySerializer
    filterset_fields = ["thread", "is_accepted"]

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        reply = self.get_object()
        ForumReply.objects.filter(thread_id=reply.thread_id, is_accepted=True).update(is_accepted=False)
        reply.is_accepted = True
        reply.save(update_fields=["is_accepted", "updated_at"])
        return Response(ForumReplySerializer(reply).data)


def _get_tenant(slug):
    try:
        return Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist:
        raise ValidationError("Forum not found.")


def _get_thread_or_404(tenant_id, thread_slug):
    try:
        return ForumThread.objects.get(tenant_id=tenant_id, slug=thread_slug)
    except ForumThread.DoesNotExist:
        raise ValidationError("Thread not found.")


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def public_thread_list(request, slug):
    """GET lists threads; POST creates one. One URL for both — a separate
    `threads/create/` route previously collided with the dynamic thread-slug
    route below it: a thread titled "Create" would slugify to "create" and
    become permanently unreachable through its own detail view, since the
    static "create" route matched first."""
    tenant = _get_tenant(slug)
    if request.method == "POST":
        serializer = PublicThreadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        thread = serializer.save(tenant_id=tenant.id)
        return Response(PublicThreadDetailSerializer(thread).data, status=201)

    threads = ForumThread.objects.filter(tenant_id=tenant.id).annotate(reply_count=Count("replies"))
    return Response(PublicThreadListSerializer(threads, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_thread_detail(request, slug, thread_slug):
    tenant = _get_tenant(slug)
    thread = _get_thread_or_404(tenant.id, thread_slug)
    return Response(PublicThreadDetailSerializer(thread).data)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def public_reply_create(request, slug, thread_slug):
    tenant = _get_tenant(slug)
    thread = _get_thread_or_404(tenant.id, thread_slug)
    if thread.is_locked:
        raise ValidationError("This thread is locked and no longer accepting replies.")
    serializer = PublicReplyCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reply = serializer.save(tenant_id=tenant.id, thread=thread)
    return Response(PublicReplySerializer(reply).data, status=201)
