"""
Staff CRUD (PageViewSet/PageBlockViewSet + drag-drop reorder) plus a
public site renderer — no login required to view a published page, same
posture as blog/forum/storefront/elearning. Public views resolve their
own tenant from the `slug` URL segment. Mounted paths are exempted from
the tenant/auth middleware — see core/middleware/tenant.py.
"""

from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.models import Tenant
from products.cycom.cms.models import Page, PageBlock
from products.cycom.cms.serializers import PageBlockSerializer, PageSerializer, PageTreeSerializer
from products.cycom.cms.services import reorder_blocks


class PageViewSet(TenantScopedModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    filterset_fields = ["is_published"]

    @action(detail=True, methods=["get"])
    def tree(self, request, pk=None):
        return Response(PageTreeSerializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        page = self.get_object()
        page.is_published = True
        page.save(update_fields=["is_published", "updated_at"])
        return Response(PageSerializer(page).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        page = self.get_object()
        page.is_published = False
        page.save(update_fields=["is_published", "updated_at"])
        return Response(PageSerializer(page).data)


class PageBlockViewSet(TenantScopedModelViewSet):
    queryset = PageBlock.objects.all()
    serializer_class = PageBlockSerializer
    filterset_fields = ["page"]

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        page_id = request.data.get("page")
        moves = request.data.get("moves")
        if not page_id or not isinstance(moves, list):
            raise ValidationError("page and moves[] are required.")
        try:
            page = Page.objects.get(id=page_id, tenant_id=request.tenant_id)
        except Page.DoesNotExist:
            raise ValidationError("Page not found.")
        reorder_blocks(page, moves, request.tenant_id)
        return Response(PageTreeSerializer(page).data)


def _get_tenant(slug):
    try:
        return Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist:
        raise ValidationError("Site not found.")


@api_view(["GET"])
@permission_classes([AllowAny])
def public_page_detail(request, slug, page_slug):
    tenant = _get_tenant(slug)
    try:
        page = Page.objects.get(tenant_id=tenant.id, slug=page_slug, is_published=True)
    except Page.DoesNotExist:
        raise ValidationError("Page not found.")
    return Response(PageTreeSerializer(page).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_homepage(request, slug):
    tenant = _get_tenant(slug)
    try:
        page = Page.objects.get(tenant_id=tenant.id, is_homepage=True, is_published=True)
    except Page.DoesNotExist:
        raise ValidationError("This site has no published homepage yet.")
    return Response(PageTreeSerializer(page).data)
