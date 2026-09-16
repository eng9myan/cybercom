from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel

# Shared by StaffLeave and LeaveEntitlement — the two must agree on the
# vocabulary or a balance would be kept against a type nobody can request.
LEAVE_TYPE_CHOICES = [
    ("annual", "Annual"),
    ("sick", "Personal/Sick"),
    ("long_service", "Long Service"),
    ("unpaid", "Unpaid"),
    ("parental", "Parental"),
]


class Staff(BaseModel):
    ROLE_CHOICES = [("teacher", "Teacher"), ("admin", "Admin"), ("support", "Support"),
                    ("leadership", "Leadership"), ("finance", "Finance"), ("other", "Other")]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    staff_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="teacher")
    department = models.CharField(max_length=100, blank=True)
    campus = models.ForeignKey("cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="staff")
    tfn = models.CharField(max_length=20, blank=True)  # tax file number (AU)
    super_fund = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_hr_staff"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Contract(BaseModel):
    TYPE_CHOICES = [("full_time", "Full Time"), ("part_time", "Part Time"),
                    ("casual", "Casual"), ("fixed_term", "Fixed Term")]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="contracts")
    contract_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="full_time")
    annual_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fte = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_hr_contracts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.staff_id} {self.contract_type} {self.annual_salary}"


class PerformanceReview(BaseModel):
    """Periodic staff performance review. Ratings are 1–5, reviewer is a human."""

    STATUS_CHOICES = [
        ("draft", "Draft"), ("submitted", "Submitted"),
        ("acknowledged", "Acknowledged by Staff"), ("closed", "Closed"),
    ]
    RATINGS = [(1, "Unsatisfactory"), (2, "Developing"), (3, "Effective"),
               (4, "Highly Effective"), (5, "Exemplary")]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="performance_reviews")
    review_period = models.CharField(max_length=50)  # e.g. "2026 Semester 1"
    review_date = models.DateField(null=True, blank=True)
    reviewer_name = models.CharField(max_length=255, blank=True)
    overall_rating = models.PositiveSmallIntegerField(choices=RATINGS, null=True, blank=True)
    strengths = models.TextField(blank=True)
    development_areas = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    staff_comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_hr_performance_reviews"
        ordering = ["-review_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "staff", "review_period"], name="uniq_review_per_staff_period"
            )
        ]

    def __str__(self):
        return f"Review {self.staff_id} {self.review_period} ({self.status})"


class OnboardingTask(BaseModel):
    """
    A checklist item in a staff onboarding or offboarding workflow (issue laptop,
    working-with-children check, revoke accounts, return keys, …).
    """

    KIND_CHOICES = [("onboarding", "Onboarding"), ("offboarding", "Offboarding")]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="onboarding_tasks")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="onboarding")
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    assigned_to = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.CharField(max_length=255, blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cyed_hr_onboarding_tasks"
        ordering = ["kind", "sequence", "created_at"]

    def __str__(self):
        return f"{self.kind}: {self.title} ({'done' if self.is_completed else 'open'})"


class StaffClearance(BaseModel):
    """
    A credential a staff member must hold, and the date it stops being valid.

    In Australia a school **must** verify a Working With Children Check and
    monitor its validity: an expired clearance has to stop classroom contact,
    not merely appear on a report. Teacher registration (VIT / NESA / TRB and
    the other state regulators) works the same way, and first-aid and
    anaphylaxis certificates are audited on the same cycle.

    Nothing in CyEd tracked any of this. The consequence was not a missing
    feature but a compliance failure: a school running this system could not
    answer "is this person's clearance current?", which is one of the two
    questions HR is asked most.

    `expires_on` is nullable because a small number of credentials genuinely do
    not expire; that is a decision the registrar makes, not a data-entry
    shortcut, so it reads as "never expires" rather than "unknown".
    """

    KIND_CHOICES = [
        ("wwcc", "Working With Children Check"),
        ("teacher_registration", "Teacher Registration"),
        ("police_check", "National Police Check"),
        ("first_aid", "First Aid"),
        ("anaphylaxis", "Anaphylaxis Management"),
        ("cpr", "CPR"),
        ("other", "Other"),
    ]
    # Credentials without which a person may not be alone with children. These
    # are the ones that block a teaching assignment when they lapse.
    BLOCKING_KINDS = {"wwcc", "teacher_registration"}

    STATUS_VALID = "valid"
    STATUS_EXPIRING = "expiring"
    STATUS_EXPIRED = "expired"
    STATUS_UNVERIFIED = "unverified"

    # A clearance inside this window is surfaced for renewal. Six weeks is
    # roughly the turnaround on a WWCC renewal in most states.
    EXPIRY_WARNING_DAYS = 42

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="clearances")
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default="wwcc")
    number = models.CharField(max_length=100, blank=True)
    issuing_state = models.CharField(max_length=10, blank=True)  # VIC, NSW, QLD, …
    issued_on = models.DateField(null=True, blank=True)
    expires_on = models.DateField(
        null=True, blank=True,
        help_text="Null means this credential does not expire — a deliberate choice, not unknown.",
    )
    # Verification is a human act: someone sighted the card against the
    # regulator's register. An unverified row is not evidence of anything.
    verified_by = models.CharField(max_length=255, blank=True)
    verified_on = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cyed_hr_clearances"
        ordering = ["staff", "kind", "-expires_on"]
        constraints = [
            # One live record per credential per person. Renewals update the
            # dates; history lives in the audit trail, not in duplicate rows
            # that make "is it current?" ambiguous.
            models.UniqueConstraint(
                fields=["tenant_id", "staff", "kind"], name="uniq_clearance_per_staff_kind"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "expires_on"], name="idx_clearance_expiry"),
        ]

    def status(self, as_at: date | None = None) -> str:
        as_at = as_at or timezone.localdate()
        if not self.verified_on:
            return self.STATUS_UNVERIFIED
        if self.expires_on is None:
            return self.STATUS_VALID
        if self.expires_on < as_at:
            return self.STATUS_EXPIRED
        if self.expires_on <= as_at + timedelta(days=self.EXPIRY_WARNING_DAYS):
            return self.STATUS_EXPIRING
        return self.STATUS_VALID

    def is_current(self, as_at: date | None = None) -> bool:
        return self.status(as_at) in (self.STATUS_VALID, self.STATUS_EXPIRING)

    def days_until_expiry(self, as_at: date | None = None):
        if self.expires_on is None:
            return None
        return (self.expires_on - (as_at or timezone.localdate())).days

    def __str__(self):
        return f"{self.staff_id} {self.get_kind_display()} ({self.status()})"


class LeaveEntitlement(BaseModel):
    """
    How much leave of one type a staff member has, for one leave year.

    `StaffLeave` recorded days taken with no entitlement, accrual or balance
    behind it, so HR could not answer "does she have leave left?" and could not
    stop an over-draw. Under the National Employment Standards a full-time
    employee accrues 4 weeks (20 days) paid annual leave and 10 days paid
    personal/carer's leave per year, pro-rata for part-timers by FTE — the
    defaults below.

    Balance is derived, never stored: `opening_balance + accrued − taken`.
    A stored balance is a number that drifts the first time a leave request is
    amended, and a drifted leave balance is one an employee will dispute.
    """

    # NES annual entitlements for a full-time employee, in days.
    NES_DAYS = {"annual": Decimal("20"), "sick": Decimal("10")}

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="entitlements")
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, default="annual")
    year = models.PositiveSmallIntegerField(help_text="Leave year, e.g. 2026.")
    # Carried over from the previous year. Annual leave carries; personal leave
    # carries too under the NES; the field exists for both.
    opening_balance = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    # Full entitlement for the year, already pro-rated by FTE.
    entitled_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_hr_leave_entitlements"
        ordering = ["-year", "leave_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "staff", "leave_type", "year"],
                name="uniq_entitlement_per_staff_type_year",
            ),
            models.CheckConstraint(
                condition=models.Q(entitled_days__gte=0), name="entitlement_days_non_negative"
            ),
        ]

    def taken_days(self) -> Decimal:
        """Days already approved against this entitlement, this leave year."""
        total = StaffLeave.objects.filter(
            tenant_id=self.tenant_id, staff_id=self.staff_id,
            leave_type=self.leave_type, status="approved",
            start_date__year=self.year,
        ).aggregate(t=models.Sum("days"))["t"]
        return Decimal(total or 0)

    def accrued_days(self, as_at: date | None = None) -> Decimal:
        """
        Entitlement earned so far this year.

        Leave accrues progressively — an employee three months into the year
        has not yet earned all four weeks. Approving against the full annual
        figure in February is how a school ends up paying out leave that was
        never earned when someone resigns in March.
        """
        as_at = as_at or timezone.localdate()
        if as_at.year > self.year:
            return Decimal(self.entitled_days)
        if as_at.year < self.year:
            return Decimal("0")
        start = date(self.year, 1, 1)
        days_in_year = Decimal((date(self.year, 12, 31) - start).days + 1)
        elapsed = Decimal((as_at - start).days + 1)
        return (Decimal(self.entitled_days) * elapsed / days_in_year).quantize(Decimal("0.01"))

    def balance(self, as_at: date | None = None) -> Decimal:
        return Decimal(self.opening_balance) + self.accrued_days(as_at) - self.taken_days()

    def __str__(self):
        return f"{self.staff_id} {self.leave_type} {self.year}: {self.balance()} days"


class StaffLeave(BaseModel):
    TYPE_CHOICES = LEAVE_TYPE_CHOICES
    STATUS_CHOICES = [("requested", "Requested"), ("approved", "Approved"), ("rejected", "Rejected")]
    # Types drawn from an accrued balance. Unpaid and parental leave are not:
    # blocking them on a balance would refuse leave an employee is entitled to.
    ACCRUED_TYPES = {"annual", "sick", "long_service"}

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="leave")
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="annual")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    reason = models.CharField(max_length=255, blank=True)
    # Set when leadership knowingly approves leave the balance does not cover.
    # An override that leaves no reason behind is indistinguishable from a bug.
    balance_override_by = models.CharField(max_length=255, blank=True)
    balance_override_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_hr_leave"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.staff_id} {self.leave_type} ({self.status})"
