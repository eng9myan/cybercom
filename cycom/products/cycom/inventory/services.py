from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.services import post_journal_entry
from products.cycom.inventory.models import SerialUnit, StockItem, StockLot


def _get_or_create_stock_item(tenant_id, product, warehouse):
    item, _ = StockItem.objects.get_or_create(
        tenant_id=tenant_id, product=product, warehouse=warehouse
    )
    return item


# ── Batch/lot + expiry tracking (tracking_mode="batch") ─────────────────────
# The StockItem aggregate above is still updated by every move regardless of
# tracking_mode — these only add the per-lot breakdown underneath it.

def _receive_lot(move):
    if not move.lot_number:
        raise ValidationError("Receipt of a batch-tracked product requires lot_number.")
    lot, _ = StockLot.objects.get_or_create(
        tenant_id=move.tenant_id, product=move.product, warehouse=move.warehouse,
        lot_number=move.lot_number, defaults={"expiry_date": move.expiry_date},
    )
    if move.expiry_date and lot.expiry_date != move.expiry_date:
        lot.expiry_date = move.expiry_date
    new_qty = lot.quantity_on_hand + move.quantity
    new_value = (lot.quantity_on_hand * lot.average_cost) + (move.quantity * move.unit_cost)
    lot.average_cost = (new_value / new_qty) if new_qty else Decimal("0")
    lot.quantity_on_hand = new_qty
    lot.save(update_fields=["expiry_date", "quantity_on_hand", "average_cost"])
    move.lot = lot


def _issue_lots(move, *, override_expired):
    """Consumes the named lot, or FEFO (earliest expiry first, no-expiry lots
    last) across lots when none is named. An expired lot blocks the issue
    unless override_expired=True — the caller (the view) is responsible for
    only setting that for an admin, same pattern as HR-2's 3-way-match
    override."""
    if move.lot_number:
        lots = list(StockLot.objects.filter(
            tenant_id=move.tenant_id, product=move.product, warehouse=move.warehouse,
            lot_number=move.lot_number,
        ))
        if not lots:
            raise ValidationError(f"No lot '{move.lot_number}' on hand at {move.warehouse}.")
    else:
        lots = list(
            StockLot.objects.filter(
                tenant_id=move.tenant_id, product=move.product, warehouse=move.warehouse,
                quantity_on_hand__gt=0,
            ).order_by(F("expiry_date").asc(nulls_last=True), "lot_number")
        )

    today = timezone.localdate()
    remaining = move.quantity
    consumed_first = None
    for lot in lots:
        if remaining <= 0:
            break
        if lot.quantity_on_hand <= 0:
            continue
        if lot.expiry_date and lot.expiry_date < today and not override_expired:
            raise ValidationError(
                f"Lot '{lot.lot_number}' expired {lot.expiry_date} — pass override_expired "
                "(admin role required) to issue it anyway."
            )
        take = min(remaining, lot.quantity_on_hand)
        lot.quantity_on_hand -= take
        lot.save(update_fields=["quantity_on_hand"])
        consumed_first = consumed_first or lot
        remaining -= take

    if remaining > 0:
        raise ValidationError(
            f"Cannot issue {move.quantity} of a batch-tracked product: "
            f"only {move.quantity - remaining} available across its lots at {move.warehouse}."
        )
    move.lot = consumed_first


# ── Serial-number tracking (tracking_mode="serial") ─────────────────────────

def _receive_serials(move):
    if len(move.serial_numbers) != move.quantity:
        raise ValidationError(
            f"Receipt of {move.quantity} serial-tracked unit(s) needs exactly that many "
            f"serial_numbers (got {len(move.serial_numbers)})."
        )
    if len(set(move.serial_numbers)) != len(move.serial_numbers):
        raise ValidationError("serial_numbers has a duplicate.")
    existing = set(SerialUnit.objects.filter(
        tenant_id=move.tenant_id, product=move.product, serial_number__in=move.serial_numbers,
    ).values_list("serial_number", flat=True))
    if existing:
        raise ValidationError(f"Serial(s) already exist for this product: {sorted(existing)}.")
    SerialUnit.objects.bulk_create([
        SerialUnit(
            tenant_id=move.tenant_id, product=move.product, warehouse=move.warehouse,
            serial_number=s, status="in_stock",
        )
        for s in move.serial_numbers
    ])


def _issue_serials(move):
    if len(move.serial_numbers) != move.quantity:
        raise ValidationError(
            f"Issue of {move.quantity} serial-tracked unit(s) needs exactly that many "
            f"serial_numbers (got {len(move.serial_numbers)})."
        )
    units = list(SerialUnit.objects.filter(
        tenant_id=move.tenant_id, product=move.product, warehouse=move.warehouse,
        serial_number__in=move.serial_numbers, status="in_stock",
    ))
    missing = set(move.serial_numbers) - {u.serial_number for u in units}
    if missing:
        raise ValidationError(f"Serial(s) not in stock at {move.warehouse}: {sorted(missing)}.")
    for unit in units:
        unit.status = "issued"
        unit.warehouse = None
        unit.sold_reference = move.reference
    SerialUnit.objects.bulk_update(units, ["status", "warehouse", "sold_reference"])


@transaction.atomic
def apply_stock_move(move, *, override_expired=False):
    """
    Applies a StockMove to the StockItem valuation ledger (weighted-average
    costing) and, where the move actually changes total inventory value
    against an outside account, posts a balanced GL entry. Transfers between
    warehouses don't touch the GL — both sides use the same product-level
    inventory_account, so a transfer's debit/credit would cancel out.

    Batch (tracking_mode="batch") and serial (tracking_mode="serial") products
    get an additional per-lot / per-unit ledger on receipt and issue — see
    _receive_lot/_issue_lots/_receive_serials/_issue_serials above. transfer
    and adjustment stay aggregate-only for tracked products for now (not a
    launch blocker — POS checkout and PO receiving, the paths that matter for
    retail, are both issue/receipt).
    """
    if move.move_type == "transfer":
        if move.status != "approved":
            raise ValidationError(f"Transfer must be approved before applying (status is '{move.status}').")
    elif move.status != "draft":
        raise ValidationError(f"Move is already '{move.status}'.")

    entry = None

    if move.move_type == "receipt":
        if move.unit_cost is None:
            raise ValidationError("Receipt requires unit_cost.")
        if not move.offset_account_id:
            raise ValidationError("Receipt requires offset_account.")
        item = _get_or_create_stock_item(move.tenant_id, move.product, move.warehouse)
        new_qty = item.quantity_on_hand + move.quantity
        new_value = (item.quantity_on_hand * item.average_cost) + (move.quantity * move.unit_cost)
        item.average_cost = (new_value / new_qty) if new_qty else Decimal("0")
        item.quantity_on_hand = new_qty
        item.save(update_fields=["quantity_on_hand", "average_cost"])

        if move.product.tracking_mode == "batch":
            _receive_lot(move)
        elif move.product.tracking_mode == "serial":
            _receive_serials(move)

        move_value = (move.quantity * move.unit_cost).quantize(Decimal("0.01"))
        entry = post_journal_entry(
            tenant_id=move.tenant_id,
            date=move.date,
            reference=move.reference or f"RCPT-{move.id}",
            lines=[
                {"account": move.product.inventory_account, "debit": move_value, "credit": 0},
                {"account": move.offset_account, "debit": 0, "credit": move_value},
            ],
            narration=f"Stock receipt: {move.product} x{move.quantity} @ {move.warehouse}",
        )

    elif move.move_type == "issue":
        if not move.offset_account_id:
            raise ValidationError("Issue requires offset_account.")
        item = _get_or_create_stock_item(move.tenant_id, move.product, move.warehouse)
        if move.quantity > item.quantity_on_hand:
            raise ValidationError(
                f"Cannot issue {move.quantity}: only {item.quantity_on_hand} on hand."
            )
        move_value = (move.quantity * item.average_cost).quantize(Decimal("0.01"))
        item.quantity_on_hand -= move.quantity
        item.save(update_fields=["quantity_on_hand"])

        if move.product.tracking_mode == "batch":
            _issue_lots(move, override_expired=override_expired)
        elif move.product.tracking_mode == "serial":
            _issue_serials(move)

        entry = post_journal_entry(
            tenant_id=move.tenant_id,
            date=move.date,
            reference=move.reference or f"ISS-{move.id}",
            lines=[
                {"account": move.offset_account, "debit": move_value, "credit": 0},
                {"account": move.product.inventory_account, "debit": 0, "credit": move_value},
            ],
            narration=f"Stock issue: {move.product} x{move.quantity} @ {move.warehouse}",
        )

    elif move.move_type == "transfer":
        if not move.destination_warehouse_id:
            raise ValidationError("Transfer requires destination_warehouse.")
        source = _get_or_create_stock_item(move.tenant_id, move.product, move.warehouse)
        if move.quantity > source.quantity_on_hand:
            raise ValidationError(
                f"Cannot transfer {move.quantity}: only {source.quantity_on_hand} on hand at {move.warehouse}."
            )
        dest = _get_or_create_stock_item(move.tenant_id, move.product, move.destination_warehouse)

        new_dest_qty = dest.quantity_on_hand + move.quantity
        new_dest_value = (dest.quantity_on_hand * dest.average_cost) + (move.quantity * source.average_cost)
        dest.average_cost = (new_dest_value / new_dest_qty) if new_dest_qty else Decimal("0")
        dest.quantity_on_hand = new_dest_qty
        dest.save(update_fields=["quantity_on_hand", "average_cost"])

        source.quantity_on_hand -= move.quantity
        source.save(update_fields=["quantity_on_hand"])

    elif move.move_type == "adjustment":
        if not move.offset_account_id:
            raise ValidationError("Adjustment requires offset_account.")
        item = _get_or_create_stock_item(move.tenant_id, move.product, move.warehouse)
        if move.quantity >= 0:
            unit_cost = move.unit_cost if move.unit_cost is not None else item.average_cost
            new_qty = item.quantity_on_hand + move.quantity
            new_value = (item.quantity_on_hand * item.average_cost) + (move.quantity * unit_cost)
            item.average_cost = (new_value / new_qty) if new_qty else Decimal("0")
            item.quantity_on_hand = new_qty
            move_value = (move.quantity * unit_cost).quantize(Decimal("0.01"))
            gl_lines = [
                {"account": move.product.inventory_account, "debit": move_value, "credit": 0},
                {"account": move.offset_account, "debit": 0, "credit": move_value},
            ]
        else:
            decrease_qty = -move.quantity
            if decrease_qty > item.quantity_on_hand:
                raise ValidationError(
                    f"Cannot adjust down by {decrease_qty}: only {item.quantity_on_hand} on hand."
                )
            move_value = (decrease_qty * item.average_cost).quantize(Decimal("0.01"))
            item.quantity_on_hand -= decrease_qty
            gl_lines = [
                {"account": move.offset_account, "debit": move_value, "credit": 0},
                {"account": move.product.inventory_account, "debit": 0, "credit": move_value},
            ]
        item.save(update_fields=["quantity_on_hand", "average_cost"])
        entry = post_journal_entry(
            tenant_id=move.tenant_id,
            date=move.date,
            reference=move.reference or f"ADJ-{move.id}",
            lines=gl_lines,
            narration=f"Stock adjustment: {move.product} {move.quantity} @ {move.warehouse}",
        )

    else:
        raise ValidationError(f"Unknown move_type '{move.move_type}'.")

    move.status = "done"
    move.journal_entry = entry
    # Compare-and-set on row_version: if a concurrent apply_stock_move() already
    # took this move to 'done', the CAS matches no rows and raises
    # OptimisticLockError, rolling back this txn (and its duplicate GL entry).
    move.save_if_unchanged(fields=["status", "journal_entry", "lot"])
    return move


@transaction.atomic
def allocate_internal_order(order, allocations: dict):
    """allocations: {line_id: qty}. submitted -> allocated."""
    if order.status != "submitted":
        raise ValidationError(f"Order must be 'submitted' to allocate; it is '{order.status}'.")
    lines = {str(l.id): l for l in order.lines.all()}
    for line_id, qty in allocations.items():
        line = lines.get(str(line_id))
        if not line:
            continue
        line.allocated_qty = min(Decimal(str(qty)), line.requested_qty)
        line.save(update_fields=["allocated_qty"])
    order.status = "allocated"
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def dispatch_internal_order(order):
    """Moves allocated stock from source to destination warehouse right now
    — the order's own allocate/dispatch steps are the approval gate, so the
    underlying StockMove is created pre-approved rather than needing a
    second, redundant transfer approval. allocated -> dispatched."""
    from products.cycom.inventory.models import StockMove

    if order.status != "allocated":
        raise ValidationError(f"Order must be 'allocated' to dispatch; it is '{order.status}'.")

    for line in order.lines.all():
        if line.allocated_qty <= 0:
            continue
        move = StockMove.objects.create(
            tenant_id=order.tenant_id,
            move_type="transfer",
            product=line.product,
            warehouse=order.source_warehouse,
            destination_warehouse=order.destination_warehouse,
            quantity=line.allocated_qty,
            date=order.required_date or order.created_at.date(),
            reference=order.number,
            status="approved",
        )
        apply_stock_move(move)
        line.shipped_qty = line.allocated_qty
        line.save(update_fields=["shipped_qty"])

    order.status = "dispatched"
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def receive_internal_order(order, receipts: dict):
    """receipts: {line_id: {received_qty, reason}}. dispatched -> received/partially_received."""
    if order.status != "dispatched":
        raise ValidationError(f"Order must be 'dispatched' to receive; it is '{order.status}'.")

    lines = {str(l.id): l for l in order.lines.all()}
    for line_id, data in receipts.items():
        line = lines.get(str(line_id))
        if not line:
            continue
        received_qty = min(Decimal(str(data.get("received_qty", 0))), line.shipped_qty)
        line.received_qty = received_qty
        line.discrepancy_reason = data.get("reason", "") if received_qty < line.shipped_qty else ""
        line.save(update_fields=["received_qty", "discrepancy_reason"])

    all_lines = order.lines.all()
    fully_received = all(l.received_qty >= l.shipped_qty for l in all_lines)
    order.status = "received" if fully_received else "partially_received"
    order.save(update_fields=["status"])
    return order
