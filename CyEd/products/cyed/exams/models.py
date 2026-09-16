"""
Exam operations: sittings, rooms, seat allocation and hall tickets.

The gradebook could record that an exam happened and what everyone scored, but
nothing organised the day itself — no seating plan, no hall tickets, no way to
know a room was over-filled until students were standing in it.

The rules encoded here are the ones exam supervision actually turns on:
capacity is a hard limit, a student sits once per sitting, and students with
access arrangements (extra time, a reader, a separate room) are placed before
everyone else rather than squeezed in afterwards.
"""

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class ExamRoom(BaseModel):
    """A space an exam can be held in, and how many desks it really has."""

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)
    capacity = models.PositiveSmallIntegerField(default=30)
    # Rows and columns drive the seat labels (A1, A2, …). Kept simple on
    # purpose: a real hall is a grid, and inventing a richer geometry would
    # buy nothing an invigilator needs.
    rows = models.PositiveSmallIntegerField(default=5)
    columns = models.PositiveSmallIntegerField(default=6)
    campus = models.ForeignKey(
        "cyed_org.Campus", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="exam_rooms",
    )
    is_accessible = models.BooleanField(
        default=False, help_text="Step-free and suitable for access arrangements."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_exam_rooms"
        ordering = ["name"]

    def seat_labels(self):
        """Every seat in the room, row-major: A1…A6, B1…B6."""
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        labels = []
        for r in range(self.rows):
            for c in range(self.columns):
                labels.append(f"{letters[r % len(letters)]}{c + 1}")
                if len(labels) >= self.capacity:
                    return labels
        return labels

    def __str__(self):
        return f"{self.name} ({self.capacity} seats)"


class ExamSitting(BaseModel):
    """One exam, at one time, that a cohort sits."""

    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("seated", "Seating allocated"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=150, blank=True)
    year_level = models.PositiveSmallIntegerField(null=True, blank=True)
    # Links back to the gradebook so results have somewhere to land.
    assessment = models.ForeignKey(
        "cyed_gradebook.Assessment", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="exam_sittings",
    )
    academic_year = models.ForeignKey(
        "cyed_sis.AcademicYear", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="exam_sittings",
    )
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    instructions = models.TextField(blank=True)
    materials_permitted = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_exam_sittings"
        ordering = ["-date", "start_time"]

    def total_capacity(self) -> int:
        return sum(a.room.capacity for a in self.room_allocations.select_related("room"))

    def __str__(self):
        return f"{self.name} on {self.date}"


class ExamRoomAllocation(BaseModel):
    """A room booked for a sitting, with its invigilator."""

    sitting = models.ForeignKey(
        ExamSitting, on_delete=models.CASCADE, related_name="room_allocations"
    )
    room = models.ForeignKey(ExamRoom, on_delete=models.PROTECT, related_name="allocations")
    invigilator = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invigilations",
    )

    class Meta:
        db_table = "cyed_exam_room_allocations"
        ordering = ["room__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["sitting", "room"], name="uniq_room_per_sitting"
            ),
        ]

    def __str__(self):
        return f"{self.room_id} for {self.sitting_id}"


class ExamCandidate(BaseModel):
    """
    One student sitting one exam: their seat, their arrangements, their ticket.

    `access_arrangement` is not decoration. A student entitled to extra time or
    a separate room has to be placed first, because seating them last means
    seating them wherever is left — which is how a child with an arrangement
    ends up without it.
    """

    ARRANGEMENT_CHOICES = [
        ("", "None"),
        ("extra_time", "Extra time"),
        ("separate_room", "Separate room"),
        ("reader", "Reader"),
        ("scribe", "Scribe"),
        ("rest_breaks", "Rest breaks"),
        ("other", "Other"),
    ]
    ATTENDANCE_CHOICES = [
        ("expected", "Expected"),
        ("present", "Present"),
        ("absent", "Absent"),
        ("withdrawn", "Withdrawn from exam"),
    ]

    sitting = models.ForeignKey(ExamSitting, on_delete=models.CASCADE, related_name="candidates")
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="exam_candidacies"
    )
    room = models.ForeignKey(
        ExamRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name="candidates"
    )
    seat_label = models.CharField(max_length=10, blank=True)
    access_arrangement = models.CharField(
        max_length=30, choices=ARRANGEMENT_CHOICES, blank=True, default=""
    )
    extra_time_minutes = models.PositiveSmallIntegerField(default=0)
    attendance = models.CharField(max_length=20, choices=ATTENDANCE_CHOICES, default="expected")
    # The ticket number a student brings to the hall. Issued once seating is
    # settled, so a ticket can never name a seat that has since changed.
    ticket_number = models.CharField(max_length=40, blank=True)
    ticket_issued_on = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_exam_candidates"
        ordering = ["room__name", "seat_label"]
        constraints = [
            models.UniqueConstraint(
                fields=["sitting", "student"], name="uniq_candidate_per_sitting"
            ),
            # Two students in one seat is the failure this table exists to
            # prevent; the database enforces it rather than the allocator.
            models.UniqueConstraint(
                fields=["sitting", "room", "seat_label"],
                condition=models.Q(seat_label__gt=""),
                name="uniq_seat_per_room_per_sitting",
            ),
        ]

    def finish_time(self, sitting=None):
        """When this candidate finishes, including any extra time."""
        sitting = sitting or self.sitting
        if not sitting.start_time:
            return None
        from datetime import datetime, timedelta

        start = datetime.combine(sitting.date, sitting.start_time)
        return (start + timedelta(
            minutes=sitting.duration_minutes + self.extra_time_minutes
        )).time()

    def __str__(self):
        return f"{self.student_id} @ {self.room_id} {self.seat_label}"
