"""
Household-level billing: sibling discounts and the consolidated family
statement.

The audit's finding was that CyEd billed *students* and had no notion of the
household that actually pays. Two consequences followed: no sibling discount
was expressible, and a parent with three children got three unrelated
statements and had to add them up themselves.

Both are fixed here, from the same source of truth — `sis.Family` — so the
discount a child receives and the statement their parent reads can never
disagree.

Design notes worth keeping:

* **Ordinals come from ENROLLED children only** (`Family.students_enrolled()`,
  eldest first). A withdrawn or graduated child must not keep occupying an
  ordinal, or the family silently keeps a discount it is no longer entitled to.
* **A child with no household is a family of one.** Not an error, not skipped:
  ordinal 1, no discount, and their bills still appear in any statement drawn
  for them. Schools import students long before they tidy up households.
* **The statement spans both ledgers.** CyEd bills through `billing.StudentBill`
  (installment plans) *and* `fees.Invoice` (ad-hoc charges). A statement that
  showed one and not the other would understate what a family owes, which is
  the one error a statement must never make.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.db.models import F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from products.cyed.billing.models import SiblingDiscountRule, StudentBill

CENT = Decimal("0.01")


def _q(x) -> Decimal:
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


# ── sibling ordinals ─────────────────────────────────────────────────────────
def sibling_ordinal(student) -> int:
    """
    This child's position among their enrolled siblings, eldest first (1-based).

    Returns 1 for a child with no household, or one whose household has no
    other enrolled children — both are genuinely "the first child" for pricing.
    """
    family = getattr(student, "family", None)
    if family is None:
        return 1
    ids = list(family.students_enrolled().values_list("id", flat=True))
    if student.id not in ids:
        # Enrolled-status children define the ordering; a withdrawn child sits
        # outside it and is charged as a first child if they are billed at all.
        return 1
    return ids.index(student.id) + 1


def resolve_rule(tenant_id, ordinal: int, *, academic_year_id=None, campus_id=None):
    """
    The rule governing a child at `ordinal`, or None.

    Picks the highest `ordinal` that does not exceed the child's, so a rule at 2
    covers the 2nd and 3rd child until a rule at 3 exists. Scope narrows from
    group-wide to campus/year: a rule naming this campus or year beats one that
    names neither, which is how a school runs a different structure at one
    campus without duplicating every rule.
    """
    if ordinal < 1:
        return None
    qs = SiblingDiscountRule.objects.filter(
        tenant_id=tenant_id, is_active=True, ordinal__lte=ordinal
    ).filter(
        Q(academic_year_id=academic_year_id) | Q(academic_year__isnull=True)
    ).filter(
        Q(campus_id=campus_id) | Q(campus__isnull=True)
    )
    best = None
    for rule in qs:
        if best is None:
            best = rule
            continue
        # Higher ordinal wins; at equal ordinal, the more specific scope wins.
        if rule.ordinal > best.ordinal:
            best = rule
        elif rule.ordinal == best.ordinal and _specificity(rule) > _specificity(best):
            best = rule
    return best


def _specificity(rule) -> int:
    return (1 if rule.academic_year_id else 0) + (1 if rule.campus_id else 0)


def sibling_discount_for_bill(bill):
    """
    Return (amount_off, rule, ordinal) for one bill.

    The discount bites only on the rule's categories, computed from the bill's
    own line items — so a family whose second child takes the bus gets the
    tuition discount and pays full transport, which is what schools actually
    intend.
    """
    student = bill.student
    ordinal = sibling_ordinal(student)
    rule = resolve_rule(
        bill.tenant_id, ordinal,
        academic_year_id=bill.academic_year_id, campus_id=bill.campus_id,
    )
    if rule is None or not rule.percent:
        return Decimal("0"), None, ordinal

    categories = rule.applies_to()
    subtotal = Decimal("0")
    for item in bill.line_items.all():
        if item.category in categories:
            subtotal += Decimal(item.amount)
    if subtotal <= 0:
        return Decimal("0"), rule, ordinal
    return _q(subtotal * Decimal(rule.percent) / Decimal("100")), rule, ordinal


def explain_bill_discount(bill) -> dict:
    """
    Why this bill costs what it does — for the statement and for the finance
    officer answering "why is my second child's invoice different from my
    neighbour's".
    """
    amount, rule, ordinal = sibling_discount_for_bill(bill)
    return {
        "sibling_ordinal": ordinal,
        "rule": rule.name if rule else None,
        "rule_id": str(rule.id) if rule else None,
        "percent": str(rule.percent) if rule else "0",
        "categories": rule.applies_to() if rule else [],
        "amount_off": str(_q(amount)),
    }


# ── family-wide operations ───────────────────────────────────────────────────
def family_bills(family):
    """Every live bill in the household, across all children."""
    return StudentBill.objects.filter(
        tenant_id=family.tenant_id, student__family=family, status__in=["draft", "active"]
    ).select_related("student", "plan", "academic_year").prefetch_related(
        "line_items", "installments__payments"
    )


def resync_family(family):
    """
    Recompute every bill in the household.

    Needed because a child's ordinal depends on their *siblings*: enrolling a
    younger child, withdrawing the eldest, or moving a student between
    households all change what someone else should pay. Without this, adding a
    third child silently leaves the second on the old rate.

    Bills with payments already recorded are not rewritten from scratch —
    `services.recalculate` locks paid installments and pushes the difference
    onto the unpaid ones, so a mid-year change never claws back money already
    taken.
    """
    from products.cyed.billing import services

    touched = 0
    for bill in family_bills(family):
        if bill.installments.exists():
            services.recalculate(bill)
            touched += 1
    return touched


def _student_rows(students, tenant_id):
    """Per-child financial position across both ledgers."""
    from products.cyed.fees.models import Invoice

    rows = []
    for student in students:
        bills = StudentBill.objects.filter(
            tenant_id=tenant_id, student=student
        ).exclude(status="cancelled").prefetch_related("line_items", "installments__payments")

        billed = paid = Decimal("0")
        overdue = Decimal("0")
        installments = []
        for bill in bills:
            for inst in bill.installments.all():
                billed += Decimal(inst.amount_due)
                paid += inst.paid_total
                if inst.status == "overdue":
                    overdue += inst.balance
                installments.append({
                    # The installment's own id, not just the bill's: a parent
                    # portal has to be able to pay a specific instalment, and
                    # without this the only handle it has is (bill, number).
                    "installment": str(inst.id),
                    "bill": str(bill.id),
                    "installment_no": inst.installment_no,
                    "due_date": inst.due_date.isoformat() if inst.due_date else None,
                    "amount_due": str(_q(inst.amount_due)),
                    "paid": str(_q(inst.paid_total)),
                    "balance": str(_q(inst.balance)),
                    "status": inst.status,
                })

        invoices = []
        for inv in Invoice.objects.filter(tenant_id=tenant_id, student=student).exclude(
            status="cancelled"
        ).prefetch_related("payments"):
            billed += Decimal(inv.amount)
            paid += inv.paid_total
            if inv.status == "overdue":
                overdue += inv.balance
            invoices.append({
                "invoice": str(inv.id),
                "description": inv.description,
                "amount": str(_q(inv.amount)),
                "paid": str(_q(inv.paid_total)),
                "balance": str(_q(inv.balance)),
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "status": inv.status,
            })

        discount = None
        active_bill = next((b for b in bills if b.status in ("draft", "active")), None)
        if active_bill is not None:
            discount = explain_bill_discount(active_bill)

        rows.append({
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "enrolment_status": student.enrolment_status,
            "sibling_discount": discount,
            "billed": str(_q(billed)),
            "paid": str(_q(paid)),
            "balance": str(_q(billed - paid)),
            "overdue": str(_q(overdue)),
            "installments": installments,
            "invoices": invoices,
        })
    return rows


def family_statement(family) -> dict:
    """
    One statement for the whole household: what each child was billed, what has
    been paid, and the single number the parent cares about — what is owed now.

    Children are listed eldest-first so the ordinals a parent sees in the
    discount column read in the same order as the rules they were quoted.
    """
    students = list(family.students_ordered())
    rows = _student_rows(students, family.tenant_id)

    billed = sum((Decimal(r["billed"]) for r in rows), Decimal("0"))
    paid = sum((Decimal(r["paid"]) for r in rows), Decimal("0"))
    overdue = sum((Decimal(r["overdue"]) for r in rows), Decimal("0"))
    discount = sum(
        (Decimal(r["sibling_discount"]["amount_off"]) for r in rows if r["sibling_discount"]),
        Decimal("0"),
    )

    return {
        "family": str(family.id),
        "name": family.name,
        "billing_email": family.billing_email(),
        "postal_address": family.postal_address(),
        "children_total": len(rows),
        "children_enrolled": family.students_enrolled().count(),
        "totals": {
            "billed": str(_q(billed)),
            "paid": str(_q(paid)),
            "balance": str(_q(billed - paid)),
            "overdue": str(_q(overdue)),
            "sibling_discount_applied": str(_q(discount)),
        },
        "children": rows,
    }


def family_balance(family) -> Decimal:
    """Just the number, for lists and dunning."""
    return Decimal(family_statement(family)["totals"]["balance"])


def family_totals_bulk(tenant_id, *, family_ids=None) -> dict:
    """
    Balance and overdue for every household, in four queries.

    The per-household path builds a full statement — every child, every
    installment, every invoice — which is right for one family on screen and
    catastrophic across all of them. Measured on a seeded year (13 campuses,
    1,650 households) the dunning sweep took 104 seconds and over 9,000
    queries because it asked for a whole statement just to read one number.

    Returns ``{family_id: {"balance": Decimal, "overdue": Decimal}}``.
    """
    from products.cyed.billing.models import Installment, InstallmentPayment
    from products.cyed.fees.models import Invoice, Payment

    money = models.DecimalField(max_digits=18, decimal_places=2)
    zero = Value(Decimal("0"))
    totals = {}

    def bucket(family_id):
        return totals.setdefault(
            str(family_id), {"balance": Decimal("0"), "overdue": Decimal("0")}
        )

    def finish():
        # A database SUM returns an unscaled Decimal. Quantising here keeps
        # these figures identical to the per-household statement's, which
        # rounds to cents — two views of the same debt disagreeing by a
        # trailing zero is the kind of thing a bursar reports as a bug.
        for entry in totals.values():
            entry["balance"] = _q(entry["balance"])
            entry["overdue"] = _q(entry["overdue"])
        return totals

    # Paid-to-date comes from a correlated subquery rather than a second join.
    # Joining payments alongside a SUM of the parent amount multiplies the
    # parent by its payment count — the row would report a family owing three
    # times what it does.
    installment_paid = Subquery(
        InstallmentPayment.objects.filter(installment=OuterRef("pk"))
        .values("installment").annotate(t=Sum("amount")).values("t")[:1],
        output_field=money,
    )
    installments = (
        Installment.objects.filter(
            tenant_id=tenant_id, bill__student__family__isnull=False
        )
        .exclude(bill__status="cancelled")
        .annotate(paid=Coalesce(installment_paid, zero, output_field=money))
        .annotate(outstanding=F("amount_due") - F("paid"))
        .values("bill__student__family_id", "status", "outstanding")
    )
    if family_ids is not None:
        installments = installments.filter(bill__student__family_id__in=family_ids)

    for row in installments:
        outstanding = Decimal(str(row["outstanding"] or 0))
        if outstanding <= 0:
            continue
        entry = bucket(row["bill__student__family_id"])
        entry["balance"] += outstanding
        if row["status"] == "overdue":
            entry["overdue"] += outstanding

    invoice_paid = Subquery(
        Payment.objects.filter(invoice=OuterRef("pk"))
        .values("invoice").annotate(t=Sum("amount")).values("t")[:1],
        output_field=money,
    )
    invoices = (
        Invoice.objects.filter(tenant_id=tenant_id, student__family__isnull=False)
        .exclude(status="cancelled")
        .annotate(paid=Coalesce(invoice_paid, zero, output_field=money))
        .annotate(outstanding=F("amount") - F("paid"))
        .values("student__family_id", "status", "outstanding")
    )
    if family_ids is not None:
        invoices = invoices.filter(student__family_id__in=family_ids)

    for row in invoices:
        outstanding = Decimal(str(row["outstanding"] or 0))
        if outstanding <= 0:
            continue
        entry = bucket(row["student__family_id"])
        entry["balance"] += outstanding
        if row["status"] == "overdue":
            entry["overdue"] += outstanding

    return finish()
