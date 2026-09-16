from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel
from products.cyed.sis.models import ClassSection, Student


class RollCall(BaseModel):
    class_section = models.ForeignKey(
        ClassSection, on_delete=models.CASCADE, related_name="roll_calls"
    )
    date = models.DateField()
    period_label = models.CharField(max_length=50, blank=True)
    taken_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_roll_calls"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["class_section", "date", "period_label"], name="uniq_rollcall_section_date_period"
            )
        ]

    def __str__(self):
        return f"{self.class_section_id} {self.date} {self.period_label}"


class AttendanceMark(BaseModel):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
        ("left_early", "Left Early"),
    ]

    roll_call = models.ForeignKey(RollCall, on_delete=models.CASCADE, related_name="marks")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_marks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="present")
    minutes_late = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_attendance_marks"
        ordering = ["student__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["roll_call", "student"], name="uniq_mark_per_student_rollcall"
            )
        ]

    def __str__(self):
        return f"{self.student_id}: {self.status}"


class EmergencyDrill(BaseModel):
    """
    One evacuation, lockdown or drill, with the roll frozen at the moment it
    started.

    Snapshotted rather than recomputed live: the roll must not shift under the
    people using it because a late student was marked present halfway through,
    and the record afterwards has to show who was expected — which a live query
    cannot reconstruct once the day has moved on.
    """

    KIND_CHOICES = [
        ("fire_drill", "Fire drill"),
        ("evacuation", "Evacuation"),
        ("lockdown", "Lockdown"),
        ("lockout", "Lockout"),
        ("other", "Other"),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="fire_drill")
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="emergency_drills",
    )
    started_at = models.DateTimeField()
    started_by = models.CharField(max_length=255, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    ended_by = models.CharField(max_length=255, blank=True)
    expected_count = models.PositiveIntegerField(default=0)
    # Frozen at close so a debrief cannot quietly lose the number that matters.
    unaccounted_at_close = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cyed_emergency_drills"
        ordering = ["-started_at"]

    def is_open(self) -> bool:
        return self.ended_at is None

    def duration_seconds(self):
        if not self.ended_at:
            return None
        return int((self.ended_at - self.started_at).total_seconds())

    def __str__(self):
        return f"{self.get_kind_display()} at {self.started_at:%Y-%m-%d %H:%M}"


class EmergencyRollEntry(BaseModel):
    """
    One person on the emergency roll.

    `state` starts at `unaccounted` for everybody. A roll that defaults to safe
    and asks staff to mark people missing produces a clean board and a wrong
    one — the whole value here is knowing precisely who has not been seen.

    Names are denormalised because this is read when the network is poor and
    joins are the first thing to time out.
    """

    STATE_CHOICES = [
        ("unaccounted", "Not yet accounted for"),
        ("safe", "Accounted for — safe"),
        ("missing", "Missing"),
    ]

    drill = models.ForeignKey(
        EmergencyDrill, on_delete=models.CASCADE, related_name="entries"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="emergency_roll_entries"
    )
    display_name = models.CharField(max_length=255)
    class_section_name = models.CharField(max_length=150, blank=True)
    # Carried onto the entry so the "who is still missing" list can show it
    # without touching the health app mid-emergency.
    has_medical_alert = models.BooleanField(default=False)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default="unaccounted")
    accounted_at = models.DateTimeField(null=True, blank=True)
    accounted_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_emergency_roll_entries"
        ordering = ["class_section_name", "display_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["drill", "student"], name="uniq_roll_entry_per_drill"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "drill", "state"], name="idx_roll_entry_state"),
        ]

    def __str__(self):
        return f"{self.display_name}: {self.state}"


class AbsenceExplanation(BaseModel):
    """
    A family's explanation for an absence, late arrival or early departure.

    The single most-used parent action in a school system, and CyEd had no way
    to receive one: a parent could see that their child was marked absent and
    could do nothing but ring the office.

    Two design points carry the weight:

    **An explanation is a claim, not a correction.** Submitting one does not
    change the attendance record — a staff member accepts or declines it, and
    only acceptance updates the mark. Attendance is a legal record that the
    department audits; letting a parent rewrite it directly would make it
    worthless as evidence and is exactly what schools fear about self-service.

    **Explanations can arrive before the absence.** "He has a dental appointment
    on Tuesday" is the common case and prevents the alert rather than answering
    it, so a planned explanation is matched to marks when the roll is taken.
    """

    REASON_CHOICES = [
        ("illness", "Illness"),
        ("medical", "Medical or dental appointment"),
        ("family", "Family reason"),
        ("bereavement", "Bereavement"),
        ("religious", "Religious observance"),
        ("travel", "Travel"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]
    KIND_CHOICES = [
        ("absence", "Absent"),
        ("late", "Late arrival"),
        ("early_departure", "Early departure"),
    ]
    # Which attendance statuses an accepted explanation may excuse. A student
    # marked present has nothing to explain.
    EXPLAINABLE = {"absent", "late", "left_early"}

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="absence_explanations"
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="absence")
    start_date = models.DateField()
    # Inclusive. A single day has end_date == start_date; a week of illness is
    # one explanation rather than five, which is how a parent thinks about it.
    end_date = models.DateField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default="illness")
    detail = models.CharField(max_length=500, blank=True)

    submitted_by_email = models.CharField(max_length=255, blank=True)
    submitted_by_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")

    reviewed_by = models.CharField(max_length=255, blank=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField(max_length=255, blank=True)
    # How many marks the acceptance actually excused. Recorded because "we
    # accepted it" and "it changed the record" are different facts, and a
    # future absence covered by a planned explanation updates this later.
    marks_updated = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cyed_absence_explanations"
        ordering = ["-start_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["tenant_id", "status", "start_date"],
                name="idx_absence_expl_queue",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="absence_explanation_dates_ordered",
            ),
        ]

    def covers(self, day) -> bool:
        return self.start_date <= day <= self.end_date

    def is_planned(self, as_at=None) -> bool:
        """Submitted for a date that has not happened yet."""
        return self.start_date > (as_at or timezone.localdate())

    def day_count(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.student_id} {self.start_date}–{self.end_date} ({self.status})"
