"""Sales → AR invoice bridge."""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner


@transaction.atomic
def create_invoice_from_order(order):
    """
    Turn a confirmed sales order into a draft customer invoice (AR).
    Resolves the customer to a Partner (created if new), maps each order line
    to an invoice line on the revenue account (4100), with AR control (1130)
    and output-tax account (2120). The invoice is left in draft — posting it
    to the GL is the existing Invoice.post action.
    """
    if order.status not in ("confirmed", "delivered"):
        raise ValidationError(f"Order is '{order.status}'; confirm it before invoicing.")
    if order.invoice_id:
        raise ValidationError("Order already has an invoice.")
    lines = list(order.lines.all())
    if not lines:
        raise ValidationError("Order has no lines to invoice.")

    tid = order.tenant_id

    def acct(code, required=True):
        a = Account.objects.filter(tenant_id=tid, code=code).first()
        if required and not a:
            raise ValidationError(f"Account {code} not found in the chart of accounts.")
        return a

    ar = acct("1130")
    revenue = acct("4100")
    tax_acct = acct("2120", required=False)

    partner, _ = Partner.objects.get_or_create(
        tenant_id=tid, name=order.customer_name,
        defaults={"partner_type": "customer", "approval_status": "approved"},
    )

    invoice = Invoice.objects.create(
        tenant_id=tid,
        invoice_type="customer",
        number=f"INV-{order.number}",
        partner=partner,
        date=order.order_date,
        due_date=order.order_date + timedelta(days=30),
        currency=order.currency,
        status="draft",
        control_account=ar,
        tax_account=tax_acct,
    )
    for l in lines:
        InvoiceLine.objects.create(
            tenant_id=tid,
            invoice=invoice,
            account=revenue,
            description=l.description or (l.product.name if l.product else "Sale"),
            quantity=l.quantity,
            unit_price=(l.unit_price * (Decimal("1") - l.discount_percent / 100)).quantize(Decimal("0.01")),
            tax_percent=l.tax_percent,
        )

    order.invoice = invoice
    order.status = "invoiced"
    order.save(update_fields=["invoice", "status", "updated_at"])
    return invoice
