from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class InterviewRound(BaseModel):
    """
    A parent–teacher interview period: "Semester 1 reporting, 12–14 August".

    Booking opens and closes on dates the school sets, because the failure mode
    is a parent booking a slot in a round that finished last term, and a
    round that never closes fills with bookings nobody is staffing.
    """

    name = models.CharField(max_length=255)
    academic_year = models.ForeignKey(
        "cyed_sis.AcademicYear", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="interview_rounds",
    )
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="interview_rounds",
    )
    bookings_open_at = models.DateTimeField()
    bookings_close_at = models.DateTimeField()
    # Stops one organised family taking every slot with a teacher before other
    # families have seen the page. The commonest complaint about these systems.
    max_bookings_per_student = models.PositiveSmallIntegerField(default=8)
    instructions = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_interview_rounds"
        ordering = ["-bookings_open_at"]

    def is_open(self, at=None) -> bool:
        at = at or timezone.now()
        return self.is_published and self.bookings_open_at <= at <= self.bookings_close_at

    def __str__(self):
        return self.name


class InterviewSlot(BaseModel):
    """
    One appointment window with one teacher.

    A slot holds at most one booking. Enforced by a unique constraint on the
    booking rather than a counter, because two parents pressing "book" at the
    same moment is exactly what happens the minute a round opens.
    """

    round = models.ForeignKey(
        InterviewRound, on_delete=models.CASCADE, related_name="slots"
    )
    teacher = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.CASCADE, related_name="interview_slots"
    )
    starts_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=10)
    location = models.CharField(max_length=150, blank=True)
    # A teacher blocking out their own break, or a slot held for a family the
    # school needs to see. Unavailable slots are never offered.
    is_available = models.BooleanField(default=True)
    blocked_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_interview_slots"
        ordering = ["starts_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "starts_at"], name="uniq_slot_per_teacher_time"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "round", "starts_at"], name="idx_slot_round_time"),
        ]

    def ends_at(self):
        return self.starts_at + timedelta(minutes=self.duration_minutes)

    def is_bookable(self, at=None) -> bool:
        return (
            self.is_available
            and self.round.is_open(at)
            and not self.bookings.filter(status="booked").exists()
        )

    def __str__(self):
        return f"{self.teacher_id} at {self.starts_at:%Y-%m-%d %H:%M}"


class InterviewBooking(BaseModel):
    """
    A family's appointment.

    Cancellations keep the row and free the slot rather than deleting it — a
    teacher wants to know a family booked and then cancelled, which reads very
    differently from never having booked.
    """

    STATUS_CHOICES = [
        ("booked", "Booked"),
        ("cancelled", "Cancelled"),
        ("attended", "Attended"),
        ("no_show", "Did not attend"),
    ]

    slot = models.ForeignKey(
        InterviewSlot, on_delete=models.CASCADE, related_name="bookings"
    )
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="interview_bookings"
    )
    booked_by_email = models.CharField(max_length=255, blank=True)
    booked_by_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="booked")
    note = models.CharField(max_length=500, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_interview_bookings"
        ordering = ["slot__starts_at"]
        constraints = [
            # The race guard: two parents pressing "book" at once means one of
            # them loses at the database, not at the application's leisure.
            models.UniqueConstraint(
                fields=["slot"],
                condition=models.Q(status="booked"),
                name="uniq_live_booking_per_slot",
            ),
        ]

    def __str__(self):
        return f"{self.student_id} → {self.slot_id} ({self.status})"


class MeetingSession(BaseModel):
    TYPES = [
        ("parent_teacher", "Parent–Teacher"),
        ("counselling", "Counselling"),
        ("staff", "Staff Meeting"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=255)
    meeting_type = models.CharField(max_length=20, choices=TYPES, default="parent_teacher")
    student = models.ForeignKey("cyed_sis.Student", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="meetings")
    participants = models.CharField(max_length=500, blank=True)
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    action_items = models.JSONField(default=list)
    key_points = models.JSONField(default=list)
    status = models.CharField(max_length=20, default="draft")  # draft / summarised
    is_confidential = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_meeting_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.meeting_type})"
