from django.db import models

from platform.common.models import BaseModel
from products.cyed.sis.models import ClassSection


class TimetableSlot(BaseModel):
    DAY_CHOICES = [
        ("mon", "Monday"),
        ("tue", "Tuesday"),
        ("wed", "Wednesday"),
        ("thu", "Thursday"),
        ("fri", "Friday"),
        ("sat", "Saturday"),
        ("sun", "Sunday"),
    ]

    class_section = models.ForeignKey(
        ClassSection, on_delete=models.CASCADE, related_name="timetable_slots"
    )
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES, default="mon")
    period_label = models.CharField(max_length=50, blank=True)  # e.g. "Period 1"
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    room = models.CharField(max_length=50, blank=True)
    # DEPRECATED: free-text fallback — see ClassSection.teacher_name. Prefer
    # `teacher` (real link to hr.Staff), falling back to `class_section.teacher`
    # when a slot doesn't carry its own override.
    teacher_name = models.CharField(max_length=255, blank=True)
    teacher = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="timetable_slots",
    )

    class Meta:
        db_table = "cyed_timetable_slots"
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.class_section_id} {self.day_of_week} {self.period_label}"

    def teacher_display(self) -> str:
        staff = self.teacher or self.class_section.teacher
        if staff:
            return f"{staff.first_name} {staff.last_name}".strip()
        return self.teacher_name or self.class_section.teacher_name
