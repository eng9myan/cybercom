from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.inventory.models import StockItem, StockMove
from products.cycom.inventory.services import apply_stock_move
from products.cycom.manufacturing.models import ManufacturingOrder, WorkCenter, WorkOrder


@transaction.atomic
def start_work_order(wo: WorkOrder) -> WorkOrder:
    if wo.status != "ready":
        raise ValidationError(f"Work order is '{wo.status}', must be 'ready' to start.")
    wo.status = "in_progress"
    wo.started_at = timezone.now()
    wo.save(update_fields=["status", "started_at", "updated_at"])

    mo = wo.manufacturing_order
    if mo.status == "draft":
        mo.status = "in_progress"
        mo.save(update_fields=["status", "updated_at"])
    return wo


@transaction.atomic
def finish_work_order(wo: WorkOrder) -> WorkOrder:
    if wo.status != "in_progress":
        raise ValidationError(f"Work order is '{wo.status}', must be 'in_progress' to finish.")
    wo.status = "done"
    wo.finished_at = timezone.now()
    wo.save(update_fields=["status", "finished_at", "updated_at"])

    next_wo = (
        WorkOrder.objects.filter(manufacturing_order=wo.manufacturing_order, sequence__gt=wo.sequence)
        .order_by("sequence")
        .first()
    )
    if next_wo and next_wo.status == "pending":
        next_wo.status = "ready"
        next_wo.save(update_fields=["status", "updated_at"])
    return wo


def work_center_load(work_center: WorkCenter, *, date_from, date_to):
    """Planned work-order minutes at this work center over a date range vs
    the work center's stated capacity — flags overallocation instead of
    silently double-booking it."""
    work_orders = WorkOrder.objects.filter(
        work_center=work_center,
        manufacturing_order__scheduled_date__gte=date_from,
        manufacturing_order__scheduled_date__lte=date_to,
    ).exclude(status="cancelled")
    planned_minutes = sum(wo.planned_duration_minutes for wo in work_orders)
    days = (date_to - date_from).days + 1
    capacity_minutes = float(work_center.capacity_per_day_hours) * 60 * days
    return {
        "work_center": work_center.name,
        "planned_minutes": planned_minutes,
        "capacity_minutes": capacity_minutes,
        "utilization_percent": (
            round((planned_minutes / capacity_minutes) * 100, 1) if capacity_minutes else None
        ),
        "overloaded": capacity_minutes > 0 and planned_minutes > capacity_minutes,
        "period": {"from": str(date_from), "to": str(date_to)},
    }


@transaction.atomic
def complete_manufacturing_order(mo: ManufacturingOrder) -> ManufacturingOrder:
    """
    Consumes each BoM component (issue moves against wip_account), then
    receives the finished product at cost = total consumed value / quantity
    produced (receipt move, same wip_account as offset) — nets the WIP
    clearing account to zero across the whole run, same absorption pattern
    described for real MRP costing: raw materials in, finished goods out.
    """
    if mo.status not in ("draft", "in_progress"):
        raise ValidationError(f"Manufacturing order must be 'draft' or 'in_progress' to complete, is '{mo.status}'.")
    if mo.routing_id and mo.work_orders.exclude(status="done").exists():
        raise ValidationError("All work orders must be completed before finishing this manufacturing order.")

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
