from django.db import models
from platform.common.models import BaseModel


class VendorQualification(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    vendor_id = models.UUIDField(db_index=True)
    qualification_type = models.CharField(max_length=100)
    expiry_date = models.DateField(null=True, blank=True)
    document_ref = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        db_table = "cycom_procurement_vendor_qualifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.qualification_type} — vendor {self.vendor_id}"


class VendorPerformance(BaseModel):
    vendor_id = models.UUIDField(db_index=True)
    evaluation_period = models.CharField(max_length=20)
    delivery_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    price_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_procurement_vendor_performances"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Vendor {self.vendor_id} — {self.evaluation_period}"
