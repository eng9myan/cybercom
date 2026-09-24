"""
Public storefront — no login. Every view here resolves its own tenant from
the `slug` URL segment (platform.tenant.models.Tenant.slug) rather than
from request.tenant_id, since there's no authenticated session to derive
it from. Mounted paths are exempted from the tenant/auth middleware the
same way platform.tenant's register/demo signup endpoints already are —
see core/middleware/tenant.py and shared/auth/auth_middleware.py.
"""

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.throttling import PublicWriteRateThrottle
from platform.tenant.models import Tenant
from products.cycom.catalog.models import Product
from products.cycom.storefront.serializers import CartSerializer, StorefrontProductSerializer
from products.cycom.storefront.services import add_to_cart, checkout, get_open_cart_or_404, remove_from_cart
from products.cycom.storefront.models import Cart


def _get_tenant(slug):
    try:
        return Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist:
        raise ValidationError("Store not found.")


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list(request, slug):
    tenant = _get_tenant(slug)
    products = Product.objects.filter(tenant_id=tenant.id, is_published_online=True, is_active=True)
    return Response(StorefrontProductSerializer(products, many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def create_cart(request, slug):
    tenant = _get_tenant(slug)
    cart = Cart.objects.create(tenant_id=tenant.id)
    return Response(CartSerializer(cart).data, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def cart_detail(request, slug, token):
    tenant = _get_tenant(slug)
    cart = get_open_cart_or_404(tenant.id, token)
    return Response(CartSerializer(cart).data)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def cart_add_item(request, slug, token):
    tenant = _get_tenant(slug)
    cart = get_open_cart_or_404(tenant.id, token)
    product_id = request.data.get("product")
    quantity = int(request.data.get("quantity", 1))
    if not product_id:
        raise ValidationError("product is required.")
    try:
        product = Product.objects.get(pk=product_id, tenant_id=tenant.id)
    except Product.DoesNotExist:
        raise ValidationError("product not found.")

    add_to_cart(cart, product=product, quantity=quantity)
    cart.refresh_from_db()
    return Response(CartSerializer(cart).data, status=201)


@api_view(["DELETE"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def cart_remove_item(request, slug, token, product_id):
    tenant = _get_tenant(slug)
    cart = get_open_cart_or_404(tenant.id, token)
    try:
        product = Product.objects.get(pk=product_id, tenant_id=tenant.id)
    except Product.DoesNotExist:
        raise ValidationError("product not found.")
    remove_from_cart(cart, product=product)
    cart.refresh_from_db()
    return Response(CartSerializer(cart).data)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def cart_checkout(request, slug, token):
    tenant = _get_tenant(slug)
    cart = get_open_cart_or_404(tenant.id, token)
    customer_name = request.data.get("customer_name")
    if not customer_name:
        raise ValidationError("customer_name is required.")
    order = checkout(cart, customer_name=customer_name, customer_email=request.data.get("customer_email", ""))
    return Response({"order_number": order.number, "total": str(order.amount_total)}, status=201)
