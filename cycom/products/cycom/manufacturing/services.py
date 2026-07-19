from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.cycom.inventory.models import StockItem, StockMove
from products.cycom.inventory.services import apply_stock_move
from products.cycom.manufacturing.models import ManufacturingOrder


@transaction.atomic
def complete_manufacturing_order(mo: ManufacturingOrder) -> ManufacturingOrder:
    """
    Consumes each BoM component (issue moves against wip_account), then
    receives the finished product at cost = total consumed value / quantity
    produced (receipt move, same wip_account as offset) — nets the WIP
    clearing account to zero across the whole run, same absorption pattern
    described for real MRP costing: raw materials in, finished goods out.
    """
    if mo.status != "draft":
        raise ValidationError(f"Manufacturing order must be 'draft' to complete, is '{mo.status}'.")

    bom = mo.bom
    runs = mo.quantity / bom.quantity
    total_consumed_value = Decimal("0")

    for line in bom.components.all():
        needed_qty = (line.quantity * runs).quantize(Decimal("0.0001"))
        item = StockItem.objects.filter(
            tenant_id=mo.tenant_id, product=line.component, warehouse=mo.warehouse
        ).first()
        available = item.quantity_on_hand if item else Decimal("0")
        if needed_qty > available:
            raise ValidationError(
                f"Cannot consume {needed_qty} of {line.component.sku}: only {available} on hand at {mo.warehouse}."
            )
        move = StockMove.objects.create(
            tenant_id=mo.tenant_id,
            move_type="issue",
            product=line.component,
            warehouse=mo.warehouse,
            quantity=needed_qty,
            date=mo.scheduled_date,
            reference=f"MO-{mo.id}-CONSUME",
            offset_account=mo.wip_account,
            status="draft",
        )
        apply_stock_move(move)
        total_consumed_value += (needed_qty * item.average_cost).quantize(Decimal("0.01"))

    unit_cost = (total_consumed_value / mo.quantity).quantize(Decimal("0.0001"))
    receipt = StockMove.objects.create(
        tenant_id=mo.tenant_id,
        move_type="receipt",
        product=bom.product,
        warehouse=mo.warehouse,
        quantity=mo.quantity,
        unit_cost=unit_cost,
        date=mo.scheduled_date,
        reference=f"MO-{mo.id}-RECEIPT",
        offset_account=mo.wip_account,
        status="draft",
    )
    apply_stock_move(receipt)

    mo.status = "done"
    mo.save(update_fields=["status", "updated_at"])
    return mo
