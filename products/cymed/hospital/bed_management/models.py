from django.db import models
from platform.common.models import BaseModel
from products.cymed.core.facilities.models import Bed
from products.cymed.core.patients.models import Patient

class BedAssignment(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_bed_assignments"

class BedOccupancy(BaseModel):
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    occupied_date = models.DateField()
    occupancy_status = models.CharField(max_length=50, default="occupied")

    class Meta:
        db_table = "cymed_hospital_bed_occupancy"

class BedReservation(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    reserved_from = models.DateTimeField()
    reserved_to = models.DateTimeField()
    status = models.CharField(max_length=50, default="pending")

    class Meta:
        db_table = "cymed_hospital_bed_reservations"

class BedCleaning(BaseModel):
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        ("scheduled", "Scheduled"), ("cleaning", "Cleaning"), ("completed", "Completed")
    ], default="scheduled")
    cleaner_name = models.CharField(max_length=255, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_hospital_bed_cleaning"

class BedMaintenance(BaseModel):
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_bed_maintenance"

class BedBlocking(BaseModel):
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    blocked_at = models.DateTimeField(auto_now_add=True)
    unblocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_bed_blocking"
