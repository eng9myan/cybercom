from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class SubstitutionPlan(BaseModel):
    DAY_CHOICES = [("mon", "Monday"), ("tue", "Tuesday"), ("wed", "Wednesday"),
                   ("thu", "Thursday"), ("fri", "Friday"), ("sat", "Saturday"), ("sun", "Sunday")]

    # DEPRECATED as an identifier: kept for display and for plans generated
    # before the FK existed. Two staff sharing a name are one string here.
    absent_teacher = models.CharField(max_length=255)
    absent_staff = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="absence_plans",
    )
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default="draft")  # draft / final
    generated_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_substitution_plans"
        ordering = ["-created_at"]

    @property
    def covered_count(self) -> int:
        return self.assignments.filter(covered=True).count()

    @property
    def gap_count(self) -> int:
        return self.assignments.filter(covered=False).count()

    def __str__(self):
        return f"Sub plan for {self.absent_teacher} ({self.day_of_week})"


class ReliefTeacher(BaseModel):
    """
    An external casual relief teacher (CRT) the school can call on.

    Flagged in the original workflow audit and open ever since: the
    substitution engine could only draw on internal staff, so a day where
    nobody was free produced an uncovered class and no next step.

    Deliberately **not** an `hr.Staff` row. A CRT is not employed by the
    school — they have no contract, no leave entitlement and no payroll record,
    and modelling them as staff would put them into every headcount, payroll
    run and leave report that exists. What they do share with staff is the
    clearance requirement, which is enforced identically below.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("do_not_book", "Do not book"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    agency = models.CharField(
        max_length=150, blank=True, help_text="Blank if they are booked directly."
    )
    # What they can cover. Free text per subject, matched loosely — a school
    # asking for "Maths" should find someone listed as "Mathematics".
    subjects = models.CharField(max_length=500, blank=True)
    year_levels = models.CharField(max_length=100, blank=True)
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    half_day_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Same clearances as employed staff. A CRT stands in front of a class, so
    # the rule cannot be weaker because the employment relationship is.
    wwcc_number = models.CharField(max_length=100, blank=True)
    wwcc_expires_on = models.DateField(null=True, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    registration_expires_on = models.DateField(null=True, blank=True)
    verified_by = models.CharField(max_length=255, blank=True)
    verified_on = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    # Set when a school does not want this person back. Kept rather than
    # deleted: the booking history has to stay intact, and "why did we stop
    # calling them" is a question that gets asked.
    do_not_book_reason = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=500, blank=True)
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="relief_teachers",
    )

    class Meta:
        db_table = "cyed_relief_teachers"
        ordering = ["last_name", "first_name"]

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def clearance_state(self, as_at=None) -> dict:
        """
        Whether this person may be put in front of children.

        A missing clearance blocks exactly like an expired one — absence of
        evidence is not evidence of a clearance, and an agency's assurance is
        not a sighted card.
        """
        as_at = as_at or timezone.localdate()
        problems = []
        if not self.verified_on:
            problems.append("clearances not verified by the school")
        if not self.wwcc_number:
            problems.append("no WWCC recorded")
        elif self.wwcc_expires_on and self.wwcc_expires_on < as_at:
            problems.append("WWCC expired")
        if not self.registration_number:
            problems.append("no teacher registration recorded")
        elif self.registration_expires_on and self.registration_expires_on < as_at:
            problems.append("teacher registration expired")
        return {"may_teach": not problems, "problems": problems}

    def may_teach(self, as_at=None) -> bool:
        return self.clearance_state(as_at)["may_teach"]

    def is_bookable(self, as_at=None) -> bool:
        return self.status == "active" and self.may_teach(as_at)

    def __str__(self):
        return f"{self.full_name()} (CRT)"


class ReliefAvailability(BaseModel):
    """
    A day a CRT has said they can work.

    Stored per-day rather than as a recurring rule because casual availability
    genuinely is per-day — a CRT who works "most Tuesdays" still declines the
    ones they are already booked for somewhere else.
    """

    relief_teacher = models.ForeignKey(
        ReliefTeacher, on_delete=models.CASCADE, related_name="availability"
    )
    date = models.DateField()
    # Blank means the whole day.
    from_time = models.TimeField(null=True, blank=True)
    to_time = models.TimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_relief_availability"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["relief_teacher", "date"], name="uniq_relief_availability_per_day"
            ),
        ]

    def __str__(self):
        return f"{self.relief_teacher_id} available {self.date}"


class ReliefBooking(BaseModel):
    """
    An offer of work to a CRT, and what came of it.

    Offer → accepted/declined, because that is how it really works: the school
    rings or texts, and the CRT says yes or no. Recording a booking as
    confirmed the moment it is made would put an uncovered class on the
    timetable board as covered.
    """

    STATUS_CHOICES = [
        ("offered", "Offered"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("cancelled", "Cancelled by school"),
        ("completed", "Completed"),
    ]

    relief_teacher = models.ForeignKey(
        ReliefTeacher, on_delete=models.PROTECT, related_name="bookings"
    )
    date = models.DateField()
    plan = models.ForeignKey(
        SubstitutionPlan, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="relief_bookings",
    )
    covering_for = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="relief_cover",
    )
    periods = models.CharField(max_length=255, blank=True, help_text="e.g. 'P1, P2, P4'")
    is_full_day = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offered")

    offered_at = models.DateTimeField(default=timezone.now)
    offered_by = models.CharField(max_length=255, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    response_note = models.CharField(max_length=255, blank=True)

    # Frozen from the CRT's rate at offer time. A rate rise next term must not
    # silently rewrite what the school already agreed to pay for a past day.
    agreed_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cost_centre = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cyed_relief_bookings"
        ordering = ["-date", "-offered_at"]
        constraints = [
            # One live booking per CRT per day. A CRT double-booked across two
            # classes is a class left standing in a corridor.
            models.UniqueConstraint(
                fields=["tenant_id", "relief_teacher", "date"],
                condition=models.Q(status__in=["offered", "accepted"]),
                name="uniq_live_relief_booking_per_day",
            ),
        ]

    def is_live(self) -> bool:
        return self.status in ("offered", "accepted")

    def __str__(self):
        return f"{self.relief_teacher_id} on {self.date} ({self.status})"


class SubstitutionAssignment(BaseModel):
    plan = models.ForeignKey(SubstitutionPlan, on_delete=models.CASCADE, related_name="assignments")
    timetable_slot = models.ForeignKey(
        "cyed_timetable.TimetableSlot", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="substitutions",
    )
    class_section_name = models.CharField(max_length=150, blank=True)
    period_label = models.CharField(max_length=50, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    room = models.CharField(max_length=50, blank=True)
    # Names are kept as the printed record — a cover sheet handed out on the
    # day should still read correctly years later even if staff records change.
    # The FKs are what the engine reasons about.
    original_teacher = models.CharField(max_length=255, blank=True)
    substitute_teacher = models.CharField(max_length=255, blank=True)
    original_staff = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="covered_away",
    )
    substitute_staff = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cover_assignments",
    )
    covered = models.BooleanField(default=False)
    # Why nobody could be found — a gap with no explanation sends a human
    # hunting through the timetable to rediscover what the engine already knew.
    gap_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_substitution_assignments"
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.period_label}: {self.original_teacher} → {self.substitute_teacher or 'UNCOVERED'}"
