from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.models import Tenant
from products.cycom.blog.models import BlogPost
from products.cycom.blog.serializers import (
    BlogPostSerializer,
    PublicBlogPostDetailSerializer,
    PublicBlogPostListSerializer,
)


class BlogPostViewSet(TenantScopedModelViewSet):
    """Authenticated staff CRUD for writing/publishing posts."""

    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    filterset_fields = ["is_published"]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        post = self.get_object()
        post.is_published = True
        post.save()
        return Response(BlogPostSerializer(post).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        post = self.get_object()
        post.is_published = False
        post.save(update_fields=["is_published", "updated_at"])
        return Response(BlogPostSerializer(post).data)


def _get_tenant(slug):
    try:
        return Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist:
        raise ValidationError("Blog not found.")


@api_view(["GET"])
@permission_classes([AllowAny])
def public_post_list(request, slug):
    tenant = _get_tenant(slug)
    posts = BlogPost.objects.filter(tenant_id=tenant.id, is_published=True)
    return Response(PublicBlogPostListSerializer(posts, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_post_detail(request, slug, post_slug):
    tenant = _get_tenant(slug)
    try:
        post = BlogPost.objects.get(tenant_id=tenant.id, slug=post_slug, is_published=True)
    except BlogPost.DoesNotExist:
        raise ValidationError("Post not found.")
    return Response(PublicBlogPostDetailSerializer(post).data)
