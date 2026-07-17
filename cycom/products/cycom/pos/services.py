from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.services import post_journal_entry
from products.cycom.inventory.models import StockMove
from products.cycom.inventory.services import apply_stock_move


@transaction.atomic
def checkout_order(order):
    if order.status != "draft":
        raise ValidationError(f"Order is already '{order.status}'.")

    lines = list(order.lines.all())
    if not lines:
        raise ValidationError("Order has no lines.")

    today = timezone.localdate()

    # Each line issues stock at the session's warehouse — reuses the same
    # weighted-average costing + GL posting as a standalone inventory issue,
    # so POS sales and manual stock issues never diverge in valuation logic.
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

    subtotal = sum((line.subtotal for line in lines), Decimal("0"))
    tax_total = sum((line.tax_amount for line in lines), Decimal("0"))
    total = subtotal + tax_total

    if tax_total and not order.tax_account_id:
        raise ValidationError("Order has tax lines but no tax_account set.")

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
