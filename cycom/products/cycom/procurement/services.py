from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.inventory.models import StockMove
from products.cycom.inventory.services import apply_stock_move
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine


@transaction.atomic
def receive_purchase_order(order: PurchaseOrder, receipts: dict | None = None):
    """
    Goods receipt (GRN). Partial or full.

    receipts: optional {line_id: qty} — receive exactly those quantities
    (each capped at the line's remaining). When omitted, every line is fully
    received. Each received quantity posts a real inventory StockMove; the PO
    lands in 'received' or 'partially_received' based on what's still owed.
    """
    if order.status not in ("approved", "partially_received"):
        raise ValidationError(f"PO must be approved before receiving; it is '{order.status}'.")

    lines = list(order.lines.select_related("product").all())
    today = timezone.localdate()

    for line in lines:
        remaining = line.quantity_remaining
        if remaining <= 0:
            continue
        if receipts is not None:
            if str(line.id) not in receipts:
                continue
            qty = min(Decimal(str(receipts[str(line.id)])), remaining)
            if qty <= 0:
                continue
        else:
            qty = remaining

        move = StockMove.objects.create(
            tenant_id=order.tenant_id,
            move_type="receipt",
            product=line.product,
            warehouse=order.warehouse,
            quantity=qty,
            unit_cost=line.unit_cost,
            date=today,
            reference=f"PO-{order.id}",
            offset_account=line.offset_account,
            status="draft",
        )
        apply_stock_move(move)
        line.quantity_received = line.quantity_received + qty
        line.save(update_fields=["quantity_received"])

    all_received = all(l.quantity_remaining <= 0 for l in PurchaseOrderLine.objects.filter(order=order))
    order.status = "received" if all_received else "partially_received"
    order.save(update_fields=["status"])
    return order


TOLERANCE = Decimal("0.01")


def three_way_match(invoice):
    """
    3-way match a vendor bill against its purchase order:
      ordered  = Σ PO line (quantity × unit_cost)
      received = Σ PO line (quantity_received × unit_cost)
      billed   = invoice subtotal (ex-tax)

    A clean match requires billed ≤ received (never pay for goods not yet
    received) and billed ≤ ordered (never pay above the PO). Anything else is
    returned as an exception for a buyer to resolve — the match never mutates
    or posts anything itself.
    """
    po = invoice.purchase_order
    if po is None:
        raise ValidationError("Bill is not linked to a purchase order.")

    lines = list(po.lines.all())
    ordered = sum((l.quantity * l.unit_cost for l in lines), Decimal("0")).quantize(Decimal("0.01"))
    received = sum((l.quantity_received * l.unit_cost for l in lines), Decimal("0")).quantize(Decimal("0.01"))
    billed = (invoice.amount_subtotal or Decimal("0")).quantize(Decimal("0.01"))

    exceptions = []
    if billed > received + TOLERANCE:
        exceptions.append(f"Billed {billed} exceeds goods received {received}.")
    if billed > ordered + TOLERANCE:
        exceptions.append(f"Billed {billed} exceeds ordered {ordered}.")
    if received + TOLERANCE < ordered:
        exceptions.append(f"Partial receipt: {received} of {ordered} received (informational).")

    return {
        "purchase_order": str(po.id),
        "ordered": ordered,
        "received": received,
        "billed": billed,
        "matched": billed <= received + TOLERANCE and billed <= ordered + TOLERANCE,
        "exceptions": exceptions,
    }
