from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.services import post_journal_entry
from products.cycom.inventory.models import StockItem, StockMove
from products.cycom.inventory.services import apply_stock_move
from products.cycom.pos.models import DISCOUNT_APPROVAL_THRESHOLD_PERCENT, POSOrderPayment


def _lines_needing_discount_approval(lines):
    return [line for line in lines if line.discount_percent > DISCOUNT_APPROVAL_THRESHOLD_PERCENT]


def submit_discount_for_approval(order):
    if order.status != "draft":
        raise ValidationError(f"Order is already '{order.status}'.")
    if not _lines_needing_discount_approval(order.lines.all()):
        raise ValidationError(
            f"No line exceeds the {DISCOUNT_APPROVAL_THRESHOLD_PERCENT}% discount threshold — approval not required."
        )
    order.discount_approval_status = "pending"
    order.discount_rejection_reason = ""
    # compare-and-set: two approvers racing this order must not both win
    order.save_if_unchanged(fields=["discount_approval_status", "discount_rejection_reason"])
    return order


def approve_discount(order, approved_by):
    if order.discount_approval_status != "pending":
        raise ValidationError(f"Discount is not pending approval (status: '{order.discount_approval_status}').")
    order.discount_approval_status = "approved"
    order.discount_approved_by = approved_by
    order.save_if_unchanged(fields=["discount_approval_status", "discount_approved_by"])
    return order


def reject_discount(order, reason=""):
    if order.discount_approval_status != "pending":
        raise ValidationError(f"Discount is not pending approval (status: '{order.discount_approval_status}').")
    order.discount_approval_status = "rejected"
    order.discount_rejection_reason = reason
    order.save_if_unchanged(fields=["discount_approval_status", "discount_rejection_reason"])
    return order


@transaction.atomic
def record_payment(order, amount, method="cash"):
    if order.order_type != "layaway":
        raise ValidationError("Advance payments only apply to layaway orders.")
    if order.status != "draft":
        raise ValidationError(f"Order is already '{order.status}'.")
    if amount is None or amount <= 0:
        raise ValidationError("amount must be positive.")
    if not order.advance_liability_account_id:
        raise ValidationError("Order has no advance_liability_account set.")

    today = timezone.localdate()
    entry = post_journal_entry(
        tenant_id=order.tenant_id,
        date=today,
        reference=order.order_number,
        lines=[
            {"account": order.cash_account, "debit": amount, "credit": 0},
            {"account": order.advance_liability_account, "debit": 0, "credit": amount},
        ],
        currency=order.currency,
        narration=f"POS advance payment {order.order_number}",
    )
    return POSOrderPayment.objects.create(
        tenant_id=order.tenant_id, order=order, amount=amount, method=method, journal_entry=entry
    )


@transaction.atomic
def checkout_order(order):
    if order.status != "draft":
        raise ValidationError(f"Order is already '{order.status}'.")

    lines = list(order.lines.all())
    if not lines:
        raise ValidationError("Order has no lines.")

    if _lines_needing_discount_approval(lines) and order.discount_approval_status != "approved":
        raise ValidationError(
            "Order has a line discount exceeding "
            f"{DISCOUNT_APPROVAL_THRESHOLD_PERCENT}% that is not approved. "
            "Submit for discount approval first."
        )

    subtotal = sum((line.subtotal for line in lines), Decimal("0"))
    tax_total = sum((line.tax_amount for line in lines), Decimal("0"))
    total = subtotal + tax_total

    if tax_total and not order.tax_account_id:
        raise ValidationError("Order has tax lines but no tax_account set.")

    is_layaway = order.order_type == "layaway"
    if is_layaway:
        if not order.advance_liability_account_id:
            raise ValidationError("Order has no advance_liability_account set.")
        amount_paid = order.amount_paid
        if amount_paid < total:
            raise ValidationError(
                f"Layaway balance still due: {total - amount_paid} of {total}. "
                "Record remaining advance payments before checkout."
            )

    today = timezone.localdate()

    # Each line issues stock at the session's warehouse — reuses the same
    # weighted-average costing + GL posting as a standalone inventory issue,
    # so POS sales and manual stock issues never diverge in valuation logic.
    # For layaway, goods are only released now (at final settlement), not
    # when the earlier advance payments were collected.
    for line in lines:
        if line.product.tracking_mode == "serial" and len(line.serial_numbers) != line.quantity:
            raise ValidationError(
                f"Line for {line.product} is serial-tracked — needs exactly "
                f"{line.quantity} serial_numbers (got {len(line.serial_numbers)})."
            )
        if line.product.requires_prescription:
            if line.prescription_id is None:
                raise ValidationError(
                    f"Line for {line.product} requires a prescription — none supplied."
                )
            if line.prescription.refills_remaining <= 0:
                raise ValidationError(
                    f"Prescription {line.prescription.rx_number or line.prescription_id} "
                    "has no refills remaining."
                )
        move = StockMove.objects.create(
            tenant_id=order.tenant_id,
            move_type="issue",
            product=line.product,
            warehouse=order.session.warehouse,
            quantity=line.quantity,
            date=today,
            reference=order.order_number,
            offset_account=order.cogs_account,
            serial_numbers=line.serial_numbers,
            status="draft",
        )
        apply_stock_move(move)
        # Capture the cost/lot this sale actually drew from — average_cost is
        # untouched by an issue, so it's still the right figure to read here.
        # A later return restocks at THIS cost/lot, not wherever the running
        # average or FEFO order has drifted to by the time of the return.
        item = StockItem.objects.get(
            tenant_id=order.tenant_id, product=line.product, warehouse=order.session.warehouse
        )
        line.unit_cost_at_sale = item.average_cost
        line.lot_number_at_sale = move.lot.lot_number if move.lot_id else ""
        line.save(update_fields=["unit_cost_at_sale", "lot_number_at_sale"])

        if line.product.requires_prescription:
            line.prescription.refills_used += 1
            line.prescription.save(update_fields=["refills_used"])

    if is_layaway:
        # Reverse the accumulated deposit liability into revenue/tax —
        # the cash side was already booked by each record_payment() call.
        gl_lines = [{"account": order.advance_liability_account, "debit": total, "credit": 0}]
    else:
        gl_lines = [{"account": order.cash_account, "debit": total, "credit": 0}]
    gl_lines.append({"account": order.revenue_account, "debit": 0, "credit": subtotal})
    if tax_total:
        gl_lines.append({"account": order.tax_account, "debit": 0, "credit": tax_total})

    entry = post_journal_entry(
        tenant_id=order.tenant_id,
        date=today,
        reference=order.order_number,
        lines=gl_lines,
        currency=order.currency,
        narration=f"POS checkout {order.order_number}",
    )

    order.amount_subtotal = subtotal
    order.amount_tax = tax_total
    order.amount_total = total
    order.status = "paid"
    order.journal_entry = entry
    order.save(
        update_fields=["amount_subtotal", "amount_tax", "amount_total", "status", "journal_entry"]
    )
    return order


# ── Returns / refunds (full or partial, line-level) ──────────────────────────

def _already_returned_qty(order_line, *, exclude_return=None):
    qs = order_line.return_lines.exclude(ret__status="rejected")
    if exclude_return is not None:
        qs = qs.exclude(ret=exclude_return)
    return sum((rl.quantity for rl in qs), Decimal("0"))


@transaction.atomic
def submit_return(order, lines, reason=""):
    """lines: [{"order_line_id": ..., "quantity": ..., "restock": bool,
    "serial_numbers": [...]}]. Only a paid order can be returned against."""
    from products.cycom.pos.models import PosReturn, PosReturnLine

    if order.status != "paid":
        raise ValidationError(f"Order is '{order.status}' — only a paid order can be returned.")
    if not lines:
        raise ValidationError("Return must have at least one line.")

    ret = PosReturn.objects.create(tenant_id=order.tenant_id, order=order, reason=reason, status="draft")
    for item in lines:
        try:
            order_line = order.lines.get(pk=item["order_line_id"])
        except order.lines.model.DoesNotExist:
            raise ValidationError(f"Line {item.get('order_line_id')} does not belong to this order.")

        qty = Decimal(str(item["quantity"]))
        if qty <= 0:
            raise ValidationError("Return quantity must be positive.")
        already = _already_returned_qty(order_line, exclude_return=ret)
        remaining = order_line.quantity - already
        if qty > remaining:
            raise ValidationError(
                f"Line {order_line.id}: can return at most {remaining} more (already returned {already})."
            )

        serials = item.get("serial_numbers", [])
        if order_line.product.tracking_mode == "serial":
            if len(serials) != qty:
                raise ValidationError(
                    f"Line {order_line.id} is serial-tracked — return needs exactly {qty} serial_numbers."
                )
            if not set(serials) <= set(order_line.serial_numbers):
                raise ValidationError(f"Line {order_line.id}: serials {serials} were not part of the original sale.")

        PosReturnLine.objects.create(
            tenant_id=order.tenant_id, ret=ret, order_line=order_line,
            quantity=qty, restock=item.get("restock", True), serial_numbers=serials,
        )

    ret.amount_subtotal = sum((l.refund_amount for l in ret.lines.all()), Decimal("0"))
    ret.amount_tax = sum((l.refund_tax for l in ret.lines.all()), Decimal("0"))
    ret.amount_total = (ret.amount_subtotal + ret.amount_tax).quantize(Decimal("0.01"))
    ret.status = "pending_approval"
    ret.save(update_fields=["amount_subtotal", "amount_tax", "amount_total", "status"])
    return ret


def reject_return(ret, reason=""):
    if ret.status != "pending_approval":
        raise ValidationError(f"Return is '{ret.status}', not pending approval.")
    ret.status = "rejected"
    ret.rejection_reason = reason
    ret.save(update_fields=["status", "rejection_reason"])
    return ret


@transaction.atomic
def approve_return(ret, *, approved_by_user_id="", approval_method="self"):
    """pending_approval -> approved: reverses the checkout GL (Dr revenue +
    tax, Cr cash) and — per line, unless restock=False (damaged goods) —
    puts the stock back at the ORIGINAL sale cost/lot/serials captured on the
    order line at checkout time. Approval authority itself (role or manager
    PIN/barcode) is the caller's (pos.views) responsibility — this assumes
    it already happened."""
    if ret.status != "pending_approval":
        raise ValidationError(f"Return is '{ret.status}', not pending approval.")

    order = ret.order
    lines = list(ret.lines.select_related("order_line", "order_line__product"))
    if not lines:
        raise ValidationError("Return has no lines.")

    refund_subtotal = sum((l.refund_amount for l in lines), Decimal("0"))
    refund_tax = sum((l.refund_tax for l in lines), Decimal("0"))
    refund_total = (refund_subtotal + refund_tax).quantize(Decimal("0.01"))

    gl_lines = [{"account": order.revenue_account, "debit": refund_subtotal, "credit": 0}]
    if refund_tax:
        if not order.tax_account_id:
            raise ValidationError("Order has a tax component but no tax_account set — cannot reverse it.")
        gl_lines.append({"account": order.tax_account, "debit": refund_tax, "credit": 0})
    gl_lines.append({"account": order.cash_account, "debit": 0, "credit": refund_total})

    today = timezone.localdate()
    entry = post_journal_entry(
        tenant_id=ret.tenant_id, date=today, reference=f"RET-{order.order_number}",
        lines=gl_lines, currency=order.currency,
        narration=f"POS return against {order.order_number}",
    )

    for rl in lines:
        if not rl.restock:
            continue
        order_line = rl.order_line
        move = StockMove.objects.create(
            tenant_id=ret.tenant_id, move_type="receipt", product=order_line.product,
            warehouse=order.session.warehouse, quantity=rl.quantity,
            unit_cost=order_line.unit_cost_at_sale or Decimal("0"),
            date=today, reference=f"RET-{order.order_number}",
            offset_account=order.cogs_account,
            lot_number=order_line.lot_number_at_sale,
            serial_numbers=rl.serial_numbers,
            status="draft",
        )
        apply_stock_move(move, is_return=True)

    ret.status = "approved"
    ret.approved_by_user_id = approved_by_user_id
    ret.approval_method = approval_method
    ret.journal_entry = entry
    ret.amount_subtotal = refund_subtotal.quantize(Decimal("0.01"))
    ret.amount_tax = refund_tax.quantize(Decimal("0.01"))
    ret.amount_total = refund_total
    ret.save(update_fields=[
        "status", "approved_by_user_id", "approval_method", "journal_entry",
        "amount_subtotal", "amount_tax", "amount_total",
    ])
    return ret
