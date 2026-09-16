"""
Installment & billing engine: build schedules from a plan, split line items
(tuition / transport / materials), reprorate when transport changes mid-year,
record payments, mark overdue, apply late fees, and send due reminders.
"""

from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

from products.cyed.billing.models import BillLineItem, Installment, InstallmentPayment, StudentBill

CENT = Decimal("0.01")


def _q(x) -> Decimal:
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


def add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, monthrange(y, m)[1]))


def discounted_total(bill) -> Decimal:
    """
    What this bill actually costs, after every discount.

    Order matters and is deliberate: the sibling discount comes off first,
    against the categories it applies to, and the upfront discount is then
    calculated on what remains. Doing it the other way round would let the two
    percentages compound onto the full tuition and hand back more than either
    policy grants.

    This is the single choke point both `generate_installments` and
    `recalculate` go through, so a discount applied here reaches new schedules
    and mid-year reproration alike — there is no second path to keep in sync.
    """
    from products.cyed.billing.family_accounts import sibling_discount_for_bill

    total = bill.total_amount

    sibling_off, _rule, _ordinal = sibling_discount_for_bill(bill)
    if sibling_off:
        total = total - sibling_off
        if total < 0:
            total = Decimal("0")

    plan = bill.plan
    if plan and plan.schedule_type == "upfront" and plan.upfront_discount_percent:
        total = total * (Decimal("1") - Decimal(plan.upfront_discount_percent) / Decimal("100"))
    return _q(total)


def _split(total: Decimal, n: int):
    """Split `total` into n amounts (cents), remainder onto the last one."""
    per = _q(total / n) if n else _q(total)
    parts = [per] * n
    if n:
        parts[-1] = _q(total - per * (n - 1))
    return parts


def _step_months(plan) -> int:
    if plan is None:
        return 1
    if plan.schedule_type == "monthly":
        return 1
    c = plan.count()
    return max(1, 12 // c) if c else 1


def generate_installments(bill, start_date=None):
    """(Re)build the full schedule from the plan. Use only before any payment."""
    bill.installments.all().delete()
    plan = bill.plan
    n = plan.count() if plan else 1
    start = start_date or bill.start_date or timezone.now().date()
    step = _step_months(plan)
    amounts = _split(discounted_total(bill), n)
    created = []
    for i in range(n):
        created.append(Installment.objects.create(
            tenant_id=bill.tenant_id, bill=bill, installment_no=i + 1,
            due_date=add_months(start, i * step), amount_due=amounts[i], status="unpaid",
        ))
    if bill.status == "draft":
        bill.status = "active"
        bill.save(update_fields=["status", "updated_at"])
    return created


def recalculate(bill):
    """
    Reprorate after a line-item change (e.g. Half→Full trip). Installments with
    payments are locked; remaining unpaid installments absorb the difference.
    """
    installments = list(bill.installments.order_by("installment_no"))
    if not installments:
        return
    total = discounted_total(bill)
    locked = [i for i in installments if i.paid_total > 0]
    unpaid = [i for i in installments if i.paid_total == 0]
    remaining = total - sum((i.amount_due for i in locked), Decimal("0"))
    if remaining < 0:
        remaining = Decimal("0")
    if unpaid:
        parts = _split(remaining, len(unpaid))
        for inst, amt in zip(unpaid, parts):
            inst.amount_due = amt
            inst.save(update_fields=["amount_due", "updated_at"])
    elif remaining > 0:
        Installment.objects.create(
            tenant_id=bill.tenant_id, bill=bill, installment_no=len(installments) + 1,
            due_date=installments[-1].due_date, amount_due=remaining, status="unpaid",
        )
    for inst in bill.installments.all():
        inst.recalc_status()


def resync_transport_line(tenant_id, student_id):
    """Upsert the transport line item on the student's active bill, then reprorate."""
    from products.cyed.transport.models import TransportSubscription

    bill = StudentBill.objects.filter(
        tenant_id=tenant_id, student_id=student_id, status__in=["draft", "active"]
    ).order_by("-created_at").first()
    if bill is None:
        return
    sub = TransportSubscription.objects.filter(
        tenant_id=tenant_id, student_id=student_id, status="active"
    ).first()
    line = bill.line_items.filter(category="transport").first()
    if sub is None:
        if line:
            line.delete()
    else:
        if line:
            line.amount = sub.fee_amount
            line.description = f"Bus — {sub.get_trip_type_display()}"
            line.save(update_fields=["amount", "description", "updated_at"])
        else:
            BillLineItem.objects.create(
                tenant_id=tenant_id, bill=bill, category="transport",
                description=f"Bus — {sub.get_trip_type_display()}", amount=sub.fee_amount,
                source_ref=str(sub.id),
            )
    recalculate(bill)


def record_payment(installment, *, amount, method="card", paid_on=None, reference=""):
    InstallmentPayment.objects.create(
        tenant_id=installment.tenant_id, installment=installment,
        amount=_q(amount), method=method, paid_on=paid_on or timezone.now().date(), reference=reference,
    )
    installment.recalc_status()
    return installment


def mark_overdue(tenant_id, today=None):
    today = today or timezone.now().date()
    n = 0
    for inst in Installment.objects.filter(tenant_id=tenant_id, status="unpaid", due_date__lt=today):
        inst.status = "overdue"
        inst.save(update_fields=["status", "updated_at"])
        n += 1
    return n


def apply_late_fees(tenant_id, today=None):
    today = today or timezone.now().date()
    applied = 0
    for inst in Installment.objects.select_related("bill__plan").filter(
        tenant_id=tenant_id, status="overdue", late_fee_applied=False, due_date__lt=today
    ):
        plan = inst.bill.plan
        pct = Decimal(plan.late_fee_percent) if plan else Decimal("0")
        if pct > 0:
            inst.amount_due = _q(Decimal(inst.amount_due) * (Decimal("1") + pct / Decimal("100")))
        inst.late_fee_applied = True
        inst.save(update_fields=["amount_due", "late_fee_applied", "updated_at"])
        applied += 1
    return applied


def send_due_reminders(tenant_id, within_days=7, today=None):
    """Notify guardians of installments due within `within_days`. Returns count."""
    from products.cyed.notifications.delivery import deliver
    from products.cyed.notifications.models import Notification

    today = today or timezone.now().date()
    horizon = today + timedelta(days=within_days)
    sent = 0
    qs = Installment.objects.select_related("bill__student").filter(
        tenant_id=tenant_id, status__in=["unpaid", "partial", "overdue"],
        due_date__gte=today, due_date__lte=horizon,
    )
    for inst in qs:
        student = inst.bill.student
        for g in student.guardians.all():
            n = Notification.objects.create(
                tenant_id=tenant_id, student=student, recipient_kind="guardian",
                recipient_name=f"{g.first_name} {g.last_name}".strip(),
                recipient_email=g.email, recipient_phone=g.phone,
                channel="in_app", category="billing",
                subject=f"Fee reminder: installment {inst.installment_no} due {inst.due_date}",
                body=f"Installment {inst.installment_no} of {student.first_name}'s fees "
                     f"({inst.balance} due) is due on {inst.due_date}.",
                related_model="cyed_billing.Installment", related_id=str(inst.id),
                status="queued",
            )
            deliver(n)
            sent += 1
    return sent
