"""
Credit notes and the defaulter escalation ladder.

Both close gaps the audit named. Credit notes were absent entirely, so a
mid-term withdrawal or a fee remission had to be handled by editing the
original bill — which destroys the record of what was billed and why it
changed. Dunning had reminders but no ladder: the same reminder repeated
forever is not a process a school can defend.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from products.cyed.billing.models import CreditNote, DunningAction, DunningCase

CENT = Decimal("0.01")


def _q(x) -> Decimal:
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


class CollectionsError(Exception):
    """A collections action was refused for a business reason (→ HTTP 400/409)."""


# ── credit notes ─────────────────────────────────────────────────────────────
def creditable_amount(*, bill=None, installment=None) -> Decimal:
    """
    The most that may still be credited against a bill or installment.

    Capped at what is actually outstanding, less any credit already issued.
    Crediting more than is owed would turn a fee ledger into a source of funds,
    which is how a billing error becomes a refund nobody authorised.
    """
    if installment is not None:
        issued = _issued_total(installment=installment)
        return max(Decimal("0"), Decimal(installment.balance) - issued)
    if bill is not None:
        issued = _issued_total(bill=bill)
        return max(Decimal("0"), Decimal(bill.balance) - issued)
    return Decimal("0")


def _issued_total(*, bill=None, installment=None) -> Decimal:
    qs = CreditNote.objects.filter(status="issued")
    if installment is not None:
        qs = qs.filter(installment=installment)
    elif bill is not None:
        qs = qs.filter(bill=bill)
    else:
        return Decimal("0")
    return sum((Decimal(n.amount) for n in qs), Decimal("0"))


def _next_number(tenant_id) -> str:
    count = CreditNote.objects.filter(tenant_id=tenant_id).count() + 1
    return f"CN-{count:06d}"


@transaction.atomic
def issue_credit_note(note, *, actor="", post_to_ledger=True):
    """
    Issue a draft note: apply the reduction, post it, and freeze the document.

    The reduction lands as a negative payment row rather than by rewriting the
    installment amount. Both ledgers derive their status from the sum of their
    payment rows, so a negative row makes the balance fall correctly through
    the ledger's own recalculation — and the original billed figure survives,
    which is the whole reason a credit note exists rather than an edit.
    """
    if note.status != "draft":
        raise CollectionsError(f"This credit note is already {note.status}.")

    amount = _q(note.amount)
    if amount <= 0:
        raise CollectionsError("A credit note must be for a positive amount.")

    available = creditable_amount(bill=note.bill, installment=note.installment)
    if (note.bill_id or note.installment_id) and amount > available:
        raise CollectionsError(
            f"Only {available} remains outstanding; crediting {amount} would put the "
            f"account in funds. Issue a refund instead if money is owed back."
        )

    note.status = "issued"
    note.issued_on = timezone.localdate()
    note.issued_by = actor[:255]
    note.number = note.number or _next_number(note.tenant_id)

    target = note.installment
    if target is None and note.bill is not None:
        # Apply to the earliest unpaid installment: a family reading the
        # statement expects a credit to clear the debt they are being chased
        # for, which is always the oldest one.
        target = note.bill.installments.exclude(status="paid").order_by(
            "installment_no"
        ).first()

    if target is not None:
        from products.cyed.billing.services import record_payment

        # A positive settlement row under the `credit_note` method: it reduces
        # what the family owes without pretending cash arrived. A negative row
        # would be a refund — it *increases* the outstanding balance, which is
        # the opposite of what a credit note does.
        record_payment(
            target, amount=amount, method="credit_note", reference=f"CN:{note.id}"
        )

    if post_to_ledger:
        note.journal_reference = _post_credit_to_ledger(note, amount)

    note.save(update_fields=[
        "status", "issued_on", "issued_by", "number", "journal_reference", "updated_at",
    ])
    return note


def _post_credit_to_ledger(note, amount):
    """
    Debit fee income, credit accounts receivable — the reverse of billing.

    Skipped rather than failed when the accounts are not configured: a school
    that has not set up its chart of accounts should still be able to credit a
    family, and a missing GL account is not a reason to keep charging someone
    for a term they did not attend.
    """
    from products.cyed.finance.models import Account
    from products.cyed.finance.services import UnbalancedEntry, post_entry

    income = Account.objects.filter(
        tenant_id=note.tenant_id, account_type="income", code__startswith="4"
    ).order_by("code").first()
    receivable = Account.objects.filter(
        tenant_id=note.tenant_id, account_type="asset", code__startswith="11"
    ).order_by("code").first()
    if income is None or receivable is None:
        return ""

    try:
        entry = post_entry(
            tenant_id=note.tenant_id,
            date=note.issued_on,
            reference=f"CN:{note.number}",
            narration=note.narration or note.get_reason_display(),
            lines=[
                {"account_id": income.id, "debit": amount, "credit": 0,
                 "description": "Fee credit"},
                {"account_id": receivable.id, "debit": 0, "credit": amount,
                 "description": "Accounts receivable"},
            ],
        )
    except UnbalancedEntry:
        return ""
    return str(entry.id)


@transaction.atomic
def cancel_credit_note(note, *, reason, actor=""):
    """
    Reverse an issued note.

    Requires a reason: "this charge was written off" and "we pretended it never
    happened" are different facts, and only one of them is true.
    """
    if note.status != "issued":
        raise CollectionsError(f"Only an issued credit note can be cancelled (this one is {note.status}).")
    if not (reason or "").strip():
        raise CollectionsError("Give a reason for cancelling the credit note.")

    from products.cyed.billing.models import InstallmentPayment
    from products.cyed.billing.services import record_payment

    applied = InstallmentPayment.objects.filter(
        tenant_id=note.tenant_id, reference=f"CN:{note.id}"
    ).first()
    if applied is not None:
        # Reverse by posting the opposite row rather than deleting the original,
        # so both movements remain visible in the ledger.
        record_payment(
            applied.installment, amount=-_q(note.amount), method="credit_note",
            reference=f"CNX:{note.id}",
        )

    note.status = "cancelled"
    note.cancelled_on = timezone.localdate()
    note.cancelled_by = actor[:255]
    note.cancel_reason = reason.strip()[:255]
    note.save(update_fields=[
        "status", "cancelled_on", "cancelled_by", "cancel_reason", "updated_at",
    ])
    return note


# ── dunning ──────────────────────────────────────────────────────────────────
def family_balance(family) -> Decimal:
    from products.cyed.billing.family_accounts import family_statement

    return Decimal(family_statement(family)["totals"]["balance"])


def family_overdue(family) -> Decimal:
    from products.cyed.billing.family_accounts import family_statement

    return Decimal(family_statement(family)["totals"]["overdue"])


def open_cases(tenant_id, *, min_overdue=Decimal("1"), as_at=None):
    """
    Open a dunning case for every household with an overdue balance that does
    not already have one. Returns the cases created.

    Balances come from `family_totals_bulk` in a handful of queries rather than
    a statement per household. Built the obvious way this took 104 seconds and
    over 9,000 queries against a seeded year — a nightly job that slow simply
    stops being run.
    """
    from products.cyed.billing.family_accounts import family_totals_bulk
    from products.cyed.sis.models import Family

    as_at = as_at or timezone.localdate()
    already_open = set(
        str(f) for f in DunningCase.objects.filter(
            tenant_id=tenant_id, status__in=["open", "paused"]
        ).values_list("family_id", flat=True)
    )
    totals = family_totals_bulk(tenant_id)

    created = []
    families = {
        str(f.id): f for f in Family.objects.filter(tenant_id=tenant_id, is_active=True)
    }
    for family_id, amounts in totals.items():
        if family_id in already_open or family_id not in families:
            continue
        if amounts["overdue"] < Decimal(min_overdue):
            continue
        created.append(DunningCase(
            tenant_id=tenant_id, family=families[family_id], stage=0, status="open",
            opened_on=as_at, opening_balance=amounts["overdue"],
            # Deliberately not set: `last_action_on` means "when the family was
            # last contacted", and opening a case contacts nobody. Stamping it
            # here would make the mandatory wait start before the first letter
            # was ever sent, delaying every case by a week for no reason.
            last_action_on=None,
        ))
    DunningCase.objects.bulk_create(created)
    return created


def can_escalate(case, as_at=None) -> tuple:
    """(allowed, reason) — the ladder's ordering and waiting rules."""
    as_at = as_at or timezone.localdate()
    if case.status == "resolved":
        return False, "This case is resolved."
    if case.status == "written_off":
        return False, "This debt has been written off."
    if case.status == "paused":
        if case.paused_until and as_at < case.paused_until:
            return False, f"This case is paused until {case.paused_until}."
        return False, "This case is paused. Resume it before escalating."
    if case.stage >= DunningCase.MAX_STAGE:
        return False, "This case is already at the final stage."
    if case.last_action_on:
        waited = (as_at - case.last_action_on).days
        if waited < DunningCase.MIN_DAYS_BETWEEN_STAGES:
            remaining = DunningCase.MIN_DAYS_BETWEEN_STAGES - waited
            return False, (
                f"The family was contacted {waited} day(s) ago. Wait {remaining} more "
                f"day(s) — escalating faster is harassment, not process."
            )
    return True, ""


@transaction.atomic
def escalate(case, *, actor="", note="", as_at=None, notify=True):
    """
    Climb one rung, recording what was done.

    Never skips a rung: a family must have been sent a reminder before they get
    a formal notice, and been offered a conversation before they are referred.
    """
    as_at = as_at or timezone.localdate()
    allowed, reason = can_escalate(case, as_at)
    if not allowed:
        raise CollectionsError(reason)

    balance = family_overdue(case.family)
    if balance <= 0:
        raise CollectionsError(
            "This household has nothing overdue. Resolve the case rather than escalating it."
        )

    case.stage += 1
    case.last_action_on = as_at
    case.save(update_fields=["stage", "last_action_on", "updated_at"])

    notification_id = ""
    if notify:
        notification_id = _notify_family(case, balance) or ""

    return DunningAction.objects.create(
        tenant_id=case.tenant_id, case=case, stage=case.stage, action_on=as_at,
        performed_by=actor[:255], balance_at_action=balance, note=note[:500],
        notification_id=notification_id,
    )


STAGE_MESSAGES = {
    1: ("Fee reminder", "a reminder that fees are outstanding"),
    2: ("Formal notice of outstanding fees", "a formal notice that fees remain outstanding"),
    3: ("Invitation to discuss outstanding fees",
        "an invitation to meet and agree a payment plan"),
    4: ("Outstanding fees referred", "notice that the account has been referred"),
}


def _notify_family(case, balance):
    """Send the stage's message to the household's billing contact."""
    from products.cyed.notifications.delivery import deliver
    from products.cyed.notifications.models import Notification

    subject, description = STAGE_MESSAGES.get(case.stage, ("Outstanding fees", "a notice"))
    email = case.family.billing_email()
    if not email:
        return None

    contact = case.family.billing_contact
    note = Notification.objects.create(
        tenant_id=case.tenant_id,
        recipient_kind="guardian",
        recipient_name=(
            f"{contact.first_name} {contact.last_name}".strip() if contact else case.family.name
        ),
        recipient_email=email,
        recipient_phone=(contact.phone if contact else ""),
        channel="in_app",
        category="billing",
        subject=subject,
        body=(
            f"This is {description}. The amount currently overdue is {balance}. "
            f"Please contact the school office to discuss payment."
        ),
        related_model="cyed_billing.DunningCase",
        related_id=str(case.id),
        status="queued",
    )
    deliver(note)
    return str(note.id)


def pause(case, *, until=None, reason="", actor=""):
    """
    Stop the letters.

    A family in genuine hardship, or one already talking to the school, should
    not keep receiving escalating notices while the conversation is happening.
    """
    if not case.is_active():
        raise CollectionsError(f"This case is {case.status} and cannot be paused.")
    case.status = "paused"
    case.paused_until = until
    case.pause_reason = (reason or "")[:255]
    case.save(update_fields=["status", "paused_until", "pause_reason", "updated_at"])
    return case


def resume(case):
    if case.status != "paused":
        raise CollectionsError("Only a paused case can be resumed.")
    case.status = "open"
    case.paused_until = None
    case.save(update_fields=["status", "paused_until", "updated_at"])
    return case


def resolve(case, *, note="", actor="", written_off=False):
    """Close a case — paid, or deliberately written off."""
    if case.status in ("resolved", "written_off"):
        raise CollectionsError(f"This case is already {case.status}.")
    case.status = "written_off" if written_off else "resolved"
    case.resolved_on = timezone.localdate()
    case.resolution_note = (note or "")[:255]
    case.save(update_fields=["status", "resolved_on", "resolution_note", "updated_at"])
    return case


def auto_resolve_settled(tenant_id):
    """
    Close cases whose household has paid. Run with the daily sweep.

    Same bulk balance lookup as `open_cases` — a household absent from the
    totals owes nothing at all, which is the commonest way a case settles.
    """
    from products.cyed.billing.family_accounts import family_totals_bulk

    cases = list(
        DunningCase.objects.select_related("family").filter(
            tenant_id=tenant_id, status__in=["open", "paused"]
        )
    )
    if not cases:
        return []

    totals = family_totals_bulk(
        tenant_id, family_ids=[c.family_id for c in cases]
    )
    closed = []
    for case in cases:
        overdue = totals.get(str(case.family_id), {}).get("overdue", Decimal("0"))
        if overdue <= 0:
            resolve(case, note="Balance settled.")
            closed.append(case)
    return closed
