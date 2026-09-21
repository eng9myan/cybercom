from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.inventory.models import Product, StockItem, Warehouse
from products.cycom.rental.models import RentalOrder, RentalOrderLine

ACTIVE_STATUSES = ("confirmed", "picked_up")


def _reserved_quantity(*, product, warehouse, start_date, end_date, exclude_line_id=None):
    overlapping = RentalOrderLine.objects.filter(
        product=product,
        warehouse=warehouse,
        order__status__in=ACTIVE_STATUSES,
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_line_id:
        overlapping = overlapping.exclude(id=exclude_line_id)
    return overlapping.aggregate(total=Sum("quantity"))["total"] or 0


@transaction.atomic
def add_rental_line(
    order: RentalOrder, *, product: Product, warehouse: Warehouse, quantity: int,
    start_date, end_date, daily_rate, late_fee_per_day=0,
) -> RentalOrderLine:
    if order.status != "draft":
        raise ValidationError(f"Order is '{order.status}', can only add lines to a draft order.")
    if end_date < start_date:
        raise ValidationError("end_date cannot be before start_date.")

    stock_item = StockItem.objects.filter(tenant_id=order.tenant_id, product=product, warehouse=warehouse).first()
    total_owned = stock_item.quantity_on_hand if stock_item else 0
    already_reserved = _reserved_quantity(
        product=product, warehouse=warehouse, start_date=start_date, end_date=end_date
    )
    if already_reserved + quantity > total_owned:
        raise ValidationError(
            f"Only {total_owned - already_reserved} of {product.sku} available at {warehouse} "
            f"for {start_date} to {end_date} (fleet size {total_owned})."
        )

    return RentalOrderLine.objects.create(
        tenant_id=order.tenant_id,
        order=order,
        product=product,
        warehouse=warehouse,
        quantity=quantity,
        start_date=start_date,
        end_date=end_date,
        daily_rate=daily_rate,
        late_fee_per_day=late_fee_per_day,
    )


def confirm_order(order: RentalOrder) -> RentalOrder:
    if order.status != "draft":
        raise ValidationError(f"Order is '{order.status}', cannot confirm.")
    if not order.lines.exists():
        raise ValidationError("Cannot confirm a rental order with no lines.")
    order.status = "confirmed"
    order.save(update_fields=["status", "updated_at"])
    return order


def pick_up_order(order: RentalOrder) -> RentalOrder:
    if order.status != "confirmed":
        raise ValidationError(f"Order is '{order.status}', must be 'confirmed' to pick up.")
    order.status = "picked_up"
    order.save(update_fields=["status", "updated_at"])
    return order


def cancel_order(order: RentalOrder) -> RentalOrder:
    if order.status not in ("draft", "confirmed"):
        raise ValidationError(f"Order is '{order.status}', cannot cancel.")
    order.status = "cancelled"
    order.save(update_fields=["status", "updated_at"])
    return order


def return_line(line: RentalOrderLine, *, returned_date=None) -> RentalOrderLine:
    if line.order.status != "picked_up":
        raise ValidationError(f"Order is '{line.order.status}', must be 'picked_up' to return items.")
    if line.returned_date:
        raise ValidationError("This line has already been returned.")

    line.returned_date = returned_date or timezone.now().date()
    line.save(update_fields=["returned_date", "updated_at"])

    order = line.order
    if not order.lines.filter(returned_date__isnull=True).exists():
        order.status = "returned"
        order.save(update_fields=["status", "updated_at"])
    return line
