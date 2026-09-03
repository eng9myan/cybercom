from django.db import models

from platform.common.models import BaseModel


class Applicant(BaseModel):
    STAGE = [
        ("new", "New"),
        ("screening", "Screening"),
        ("interview", "Interview"),
        ("offer", "Offer"),
        ("hired", "Hired"),
        ("rejected", "Rejected"),
    ]
    PRIORITY = [("0", "Normal"), ("1", "Good"), ("2", "Very Good"), ("3", "Excellent")]

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=255)
    stage = models.CharField(max_length=20, choices=STAGE, default="new")
    priority = models.CharField(max_length=2, choices=PRIORITY, default="0")
    source = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_recruitment_applicants"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.job_title}"
