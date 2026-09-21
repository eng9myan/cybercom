import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.catalog.models import Product
from products.cycom.sales.models import SalesOrder, SalesOrderLine
from products.cycom.storefront.models import Cart, CartLine


def get_open_cart_or_404(tenant_id, token: str) -> Cart:
    try:
        return Cart.objects.get(tenant_id=tenant_id, token=token)
    except Cart.DoesNotExist:
        raise ValidationError("Cart not found.")


@transaction.atomic
def add_to_cart(cart: Cart, *, product: Product, quantity: int) -> CartLine:
    if cart.status != "open":
        raise ValidationError(f"Cart is '{cart.status}', cannot modify.")
    if product.tenant_id != cart.tenant_id:
        raise ValidationError("Product does not belong to this store.")
    if not product.is_published_online:
        raise ValidationError(f"'{product.name}' is not available in this store.")
    if quantity < 1:
        raise ValidationError("quantity must be at least 1.")

    line, _created = CartLine.objects.get_or_create(
        tenant_id=cart.tenant_id, cart=cart, product=product, defaults={"quantity": quantity}
    )
    if not _created:
        line.quantity = quantity
        line.save(update_fields=["quantity", "updated_at"])
    return line


def remove_from_cart(cart: Cart, *, product: Product) -> None:
    if cart.status != "open":
        raise ValidationError(f"Cart is '{cart.status}', cannot modify.")
    CartLine.objects.filter(cart=cart, product=product).delete()


@transaction.atomic
def checkout(cart: Cart, *, customer_name: str, customer_email: str = "") -> SalesOrder:
    if cart.status != "open":
        raise ValidationError(f"Cart is '{cart.status}', cannot check out.")
    lines = list(cart.lines.select_related("product"))
    if not lines:
        raise ValidationError("Cart is empty.")

    order = SalesOrder.objects.create(
        tenant_id=cart.tenant_id,
        number=f"WEB-{uuid.uuid4().hex[:10].upper()}",
        customer_name=customer_name,
        customer_type="retail",
        order_date=timezone.now().date(),
        status="confirmed",
    )
    for line in lines:
        product = line.product
        SalesOrderLine.objects.create(
            tenant_id=cart.tenant_id,
            order=order,
            product=product,
            description=product.name,
            quantity=line.quantity,
            unit_price=product.sell_price,
            tax_percent=(product.tax_class.rate * 100) if product.tax_class_id else 0,
        )
    order.recompute_totals()

    cart.status = "checked_out"
    cart.customer_name = customer_name
    cart.customer_email = customer_email
    cart.order = order
    cart.save(update_fields=["status", "customer_name", "customer_email", "order", "updated_at"])
    return order
