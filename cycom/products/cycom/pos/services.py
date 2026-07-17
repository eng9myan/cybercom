from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.services import post_journal_entry
from products.cycom.inventory.models import StockMove
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
    order.save(update_fields=["discount_approval_status", "discount_rejection_reason"])
    return order


def approve_discount(order, approved_by):
    if order.discount_approval_status != "pending":
        raise ValidationError(f"Discount is not pending approval (status: '{order.discount_approval_status}').")
    order.discount_approval_status = "approved"
    order.discount_approved_by = approved_by
    order.save(update_fields=["discount_approval_status", "discount_approved_by"])
    return order


def reject_discount(order, reason=""):
    if order.discount_approval_status != "pending":
        raise ValidationError(f"Discount is not pending approval (status: '{order.discount_approval_status}').")
    order.discount_approval_status = "rejected"
    order.discount_rejection_reason = reason
    order.save(update_fields=["discount_approval_status", "discount_rejection_reason"])
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
        move = StockMove.objects.create(
            tenant_id=order.tenant_id,
            move_type="issue",
            product=line.product,
            warehouse=order.session.warehouse,
            quantity=line.quantity,
            date=today,
            reference=order.order_number,
            offset_account=order.cogs_account,
            status="draft",
        )
        apply_stock_move(move)

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
