from django.db import models

from platform.common.models import BaseModel
from products.cycom.hr.models import Employee
from products.cycom.recruitment.models import Applicant


class Referral(BaseModel):
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("screening", "Screening"),
        ("interviewing", "Interviewing"),
        ("hired", "Hired"),
        ("rejected", "Rejected"),
    ]

    referrer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="referrals")
    # Set once the candidate actually enters the recruitment pipeline —
    # a referral can be submitted before an Applicant record exists.
    applicant = models.ForeignKey(
        Applicant, on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals"
    )
    candidate_name = models.CharField(max_length=255)
    candidate_email = models.EmailField(blank=True)
    candidate_phone = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_referrals"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.candidate_name} referred by {self.referrer}"
