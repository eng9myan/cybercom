from decimal import Decimal

from django.db import models
from django.db.models import Sum

from platform.common.models import BaseModel


class FeePlan(BaseModel):
    SCHEDULE_TYPES = [
        ("upfront", "Full Upfront"),
        ("monthly", "Monthly"),
        ("termly", "Termly (3)"),
        ("quarterly", "Quarterly (4)"),
        ("custom", "Custom"),
    ]

    name = models.CharField(max_length=150)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default="termly")
    installments_count = models.PositiveSmallIntegerField(default=3)  # used for monthly/custom
    upfront_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    late_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_fee_plans"
        ordering = ["name"]

    def count(self) -> int:
        return {"upfront": 1, "termly": 3, "quarterly": 4}.get(
            self.schedule_type, self.installments_count or 1
        )

    def __str__(self):
        return f"{self.name} ({self.schedule_type})"


class SiblingDiscountRule(BaseModel):
    """
    "Second child 10% off tuition, third and beyond 20%."

    Rules are keyed by the child's ORDINAL within their household, counting
    enrolled children eldest-first. Resolution takes the rule with the highest
    `ordinal` that is still <= the child's ordinal, so a school that writes a
    rule at 2 and a rule at 4 automatically gets 2–3 on the first and 4+ on the
    second. That means "and beyond" needs no flag and cannot be forgotten.

    Ordinal 1 normally has no rule — the eldest pays full fees. Creating one is
    allowed (some schools discount every child once there are two) and is the
    reason the field is not constrained to >= 2.

    `categories` limits what the discount bites on. Schools discount tuition,
    not the bus: a family that gets 20% off a transport subscription is a
    revenue leak, so the default is tuition only.
    """

    name = models.CharField(max_length=150)
    ordinal = models.PositiveSmallIntegerField(
        help_text="Applies to this child and every later one, until a higher rule takes over."
    )
    percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    categories = models.JSONField(
        default=list, blank=True,
        help_text='Bill line-item categories the discount applies to. Empty = ["tuition"].',
    )
    academic_year = models.ForeignKey(
        "cyed_sis.AcademicYear", on_delete=models.CASCADE, null=True, blank=True,
        related_name="sibling_discount_rules",
        help_text="Restrict to one year. Null applies to every year.",
    )
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.CASCADE, null=True, blank=True,
        related_name="sibling_discount_rules",
        help_text="Restrict to one campus. Null applies group-wide.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_sibling_discount_rules"
        ordering = ["-ordinal"]
        constraints = [
            # Two active rules at the same ordinal and scope would make the
            # discount depend on row order, and a parent asking "why is my
            # second child 10% and my neighbour's 15%" would have no answer.
            models.UniqueConstraint(
                fields=["tenant_id", "ordinal", "academic_year", "campus"],
                name="uniq_sibling_rule_scope",
            ),
            models.CheckConstraint(
                condition=models.Q(percent__gte=0) & models.Q(percent__lte=100),
                name="sibling_discount_percent_range",
            ),
            models.CheckConstraint(
                condition=models.Q(ordinal__gte=1), name="sibling_discount_ordinal_positive"
            ),
        ]

    DEFAULT_CATEGORIES = ["tuition"]

    def applies_to(self) -> list:
        return list(self.categories) if self.categories else list(self.DEFAULT_CATEGORIES)

    def __str__(self):
        return f"{self.name}: child #{self.ordinal}+ −{self.percent}%"


class StudentBill(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("settled", "Settled"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey("cyed_sis.Student", on_delete=models.CASCADE, related_name="bills")
    academic_year = models.ForeignKey(
        "cyed_sis.AcademicYear", on_delete=models.SET_NULL, null=True, blank=True, related_name="bills"
    )
    plan = models.ForeignKey(FeePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="bills")
    campus = models.ForeignKey("cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="bills")
    currency = models.CharField(max_length=10, default="AUD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    start_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cyed_student_bills"
        ordering = ["-created_at"]

    @property
    def total_amount(self) -> Decimal:
        return self.line_items.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    @property
    def paid_amount(self) -> Decimal:
        total = Decimal("0")
        for inst in self.installments.all():
            total += inst.paid_total
        return total

    @property
    def balance(self) -> Decimal:
        # Installment amounts (post-discount) minus what has been paid.
        billed = self.installments.aggregate(t=Sum("amount_due"))["t"] or Decimal("0")
        return billed - self.paid_amount

    def __str__(self):
        return f"Bill {self.student_id} ({self.status})"


class BillLineItem(BaseModel):
    CATEGORIES = [
        ("tuition", "Tuition"),
        ("transport", "Transport"),
        ("material", "Materials"),
        ("other", "Other"),
    ]

    bill = models.ForeignKey(StudentBill, on_delete=models.CASCADE, related_name="line_items")
    category = models.CharField(max_length=20, choices=CATEGORIES, default="tuition")
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    source_ref = models.CharField(max_length=64, blank=True)  # e.g. transport subscription id

    class Meta:
        db_table = "cyed_bill_line_items"
        ordering = ["category"]

    def __str__(self):
        return f"{self.category}: {self.amount}"


class Installment(BaseModel):
    STATUS_CHOICES = [
        ("unpaid", "Unpaid"),
        ("partial", "Partially Paid"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    ]

    bill = models.ForeignKey(StudentBill, on_delete=models.CASCADE, related_name="installments")
    installment_no = models.PositiveSmallIntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unpaid")
    late_fee_applied = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_installments"
        ordering = ["installment_no"]
        constraints = [
            models.UniqueConstraint(fields=["bill", "installment_no"], name="uniq_installment_no_per_bill")
        ]

    @property
    def paid_total(self) -> Decimal:
        return self.payments.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    @property
    def balance(self) -> Decimal:
        return Decimal(self.amount_due) - self.paid_total

    def recalc_status(self, today=None):
        paid = self.paid_total
        if paid >= Decimal(self.amount_due) and self.amount_due > 0:
            self.status = "paid"
        elif paid > 0:
            self.status = "partial"
        else:
            self.status = "unpaid"
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"Installment {self.installment_no}/{self.bill_id}: {self.amount_due} ({self.status})"


class CreditNote(BaseModel):
    """
    A reduction of what a family owes, issued as its own document.

    Distinct from a refund, and the distinction is the point: a refund moves
    money back out, a credit note says the money was never owed. A mid-term
    withdrawal, a fee remission, a hardship concession and a mis-billed charge
    are all credit notes, and editing the original bill instead would destroy
    the audit trail of what was billed and why it changed.

    Issued notes are immutable. Cancelling one is itself an act with a reason,
    because "this charge was written off" and "we pretended it never happened"
    are different facts and only one of them is true.
    """

    REASON_CHOICES = [
        ("withdrawal", "Student withdrew"),
        ("remission", "Fee remission / scholarship"),
        ("hardship", "Financial hardship concession"),
        ("billing_error", "Billing error"),
        ("goodwill", "Goodwill"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.PROTECT, related_name="credit_notes"
    )
    # What is being credited. A note may sit against a whole bill or a single
    # installment; both are optional so a standalone concession is expressible.
    bill = models.ForeignKey(
        StudentBill, on_delete=models.PROTECT, null=True, blank=True, related_name="credit_notes"
    )
    installment = models.ForeignKey(
        "Installment", on_delete=models.PROTECT, null=True, blank=True,
        related_name="credit_notes",
    )
    number = models.CharField(max_length=40, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, default="other")
    narration = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    issued_on = models.DateField(null=True, blank=True)
    issued_by = models.CharField(max_length=255, blank=True)
    cancelled_on = models.DateField(null=True, blank=True)
    cancelled_by = models.CharField(max_length=255, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    # Set once the reduction has been posted to the general ledger.
    journal_reference = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "cyed_credit_notes"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="credit_note_amount_positive"
            ),
        ]

    def is_effective(self) -> bool:
        """Only an issued note reduces a balance. Drafts and cancellations do not."""
        return self.status == "issued"

    def __str__(self):
        return f"Credit {self.number or self.id} {self.amount} ({self.status})"


class InstallmentPayment(BaseModel):
    METHOD_CHOICES = [
        ("card", "Card"), ("bank_transfer", "Bank Transfer"), ("bpay", "BPAY"),
        ("direct_debit", "Direct Debit"), ("cash", "Cash"),
        # A credit note settles a debt without money changing hands. It has to
        # be a distinct method, not recorded as cash: banking and cash-flow
        # reports read these rows, and a remission booked as "cash" is money
        # the school will look for in its account and never find.
        ("credit_note", "Credit note"),
    ]
    # Methods that represent real money in or out, for cash reporting.
    CASH_METHODS = {"card", "bank_transfer", "bpay", "direct_debit", "cash"}

    installment = models.ForeignKey(Installment, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="card")
    paid_on = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cyed_installment_payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.amount} on {self.installment_id}"


class DunningCase(BaseModel):
    """
    An overdue debt being worked through a staged escalation ladder.

    Reminders already existed, but a reminder repeated forever is not a
    process. A school chasing school fees has to be able to show what it did
    and when — a reminder, then a formal notice, then an offer to talk, and
    only then a referral — because skipping straight to debt collection over
    a family's children is both unfair and, in most jurisdictions, indefensible.

    The ladder therefore enforces order and a minimum wait between rungs. A
    case can always be paused (a family in genuine hardship should not keep
    receiving letters) or resolved.
    """

    STAGE_CHOICES = [
        (0, "Opened"),
        (1, "Reminder sent"),
        (2, "Formal notice"),
        (3, "Meeting / payment plan offered"),
        (4, "Referred"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("paused", "Paused"),
        ("resolved", "Resolved"),
        ("written_off", "Written off"),
    ]
    # A family must be given time to respond before the next rung. Escalating
    # twice in a day is harassment, not process.
    MIN_DAYS_BETWEEN_STAGES = 7
    MAX_STAGE = 4

    family = models.ForeignKey(
        "cyed_sis.Family", on_delete=models.CASCADE, related_name="dunning_cases"
    )
    stage = models.PositiveSmallIntegerField(choices=STAGE_CHOICES, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    opened_on = models.DateField(null=True, blank=True)
    # Balance when the case was opened, kept so the history shows what was
    # being chased even after the debt is settled.
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_action_on = models.DateField(null=True, blank=True)
    paused_until = models.DateField(null=True, blank=True)
    pause_reason = models.CharField(max_length=255, blank=True)
    resolved_on = models.DateField(null=True, blank=True)
    resolution_note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_dunning_cases"
        ordering = ["-created_at"]
        constraints = [
            # One live case per household; a second would double every letter.
            models.UniqueConstraint(
                fields=["tenant_id", "family"], name="uniq_open_dunning_case_per_family",
                condition=models.Q(status__in=["open", "paused"]),
            ),
        ]

    def is_active(self) -> bool:
        return self.status in ("open", "paused")

    def __str__(self):
        return f"Dunning {self.family_id} stage {self.stage} ({self.status})"


class DunningAction(BaseModel):
    """
    One rung actually climbed: what was done, by whom, when.

    Recorded separately from the case's current stage because the case shows
    where things stand and this shows what happened — and it is the second one
    a school has to produce when a family disputes the process.
    """

    case = models.ForeignKey(DunningCase, on_delete=models.CASCADE, related_name="actions")
    stage = models.PositiveSmallIntegerField(choices=DunningCase.STAGE_CHOICES)
    action_on = models.DateField()
    performed_by = models.CharField(max_length=255, blank=True)
    balance_at_action = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=500, blank=True)
    notification_id = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "cyed_dunning_actions"
        ordering = ["action_on", "stage"]

    def __str__(self):
        return f"{self.get_stage_display()} on {self.action_on}"
