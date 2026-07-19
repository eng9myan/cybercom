from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.ar_ap.models import Invoice, InvoiceLine
from products.cycom.subscriptions.models import Subscription


def generate_invoice(subscription: Subscription) -> Invoice:
    """
    Creates a DRAFT customer invoice for the current billing period and
    advances next_billing_date. Posting the invoice (GL entry) reuses
    ar_ap's own InvoiceViewSet.post_invoice action — not duplicated here.
    """
    if subscription.status != "active":
        raise ValidationError(f"Subscription must be 'active' to bill, is '{subscription.status}'.")

    plan = subscription.plan
    invoice = Invoice.objects.create(
        tenant_id=subscription.tenant_id,
        invoice_type="customer",
        number=f"SUB-{subscription.id}-{subscription.next_billing_date.isoformat()}",
        partner=subscription.customer,
        date=subscription.next_billing_date,
        due_date=subscription.next_billing_date,
        currency=plan.currency,
        control_account=subscription.control_account,
    )
    InvoiceLine.objects.create(
        tenant_id=subscription.tenant_id,
        invoice=invoice,
        account=plan.revenue_account,
        description=f"{plan.name} — {plan.billing_interval} subscription",
        quantity=1,
        unit_price=plan.price,
    )

    subscription.next_billing_date = plan.next_date_after(subscription.next_billing_date)
    subscription.save(update_fields=["next_billing_date", "updated_at"])
    return invoice


def pause_subscription(subscription: Subscription) -> Subscription:
    if subscription.status != "active":
        raise ValidationError(f"Subscription must be 'active' to pause, is '{subscription.status}'.")
    subscription.status = "paused"
    subscription.save(update_fields=["status", "updated_at"])
    return subscription


def resume_subscription(subscription: Subscription) -> Subscription:
    if subscription.status != "paused":
        raise ValidationError(f"Subscription must be 'paused' to resume, is '{subscription.status}'.")
    subscription.status = "active"
    subscription.save(update_fields=["status", "updated_at"])
    return subscription


def cancel_subscription(subscription: Subscription) -> Subscription:
    if subscription.status == "cancelled":
        raise ValidationError("Subscription is already cancelled.")
    subscription.status = "cancelled"
    subscription.cancelled_at = timezone.now()
    subscription.save(update_fields=["status", "cancelled_at", "updated_at"])
    return subscription
