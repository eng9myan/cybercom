from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.inventory.models import StockMove
from products.cycom.inventory.services import apply_stock_move
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine


@transaction.atomic
def receive_purchase_order(order: PurchaseOrder):
    if order.status not in ("approved", "partially_received"):
        raise ValidationError(f"PO must be approved before receiving; it is '{order.status}'.")

    lines = list(order.lines.select_related("product").all())
    today = timezone.localdate()

    for line in lines:
        remaining = line.quantity_remaining
        if remaining <= 0:
            continue
        move = StockMove.objects.create(
            tenant_id=order.tenant_id,
            move_type="receipt",
            product=line.product,
            warehouse=order.warehouse,
            quantity=remaining,
            unit_cost=line.unit_cost,
            date=today,
            reference=f"PO-{order.id}",
            offset_account=line.offset_account,
            status="draft",
        )
        apply_stock_move(move)
        line.quantity_received = line.quantity
        line.save(update_fields=["quantity_received"])

    all_received = all(l.quantity_remaining <= 0 for l in PurchaseOrderLine.objects.filter(order=order))
    order.status = "received" if all_received else "partially_received"
    order.save(update_fields=["status"])
    return order
