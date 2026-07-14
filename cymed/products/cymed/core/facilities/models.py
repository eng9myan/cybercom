from django.db import models

from platform.common.models import BaseModel
from products.cymed.core.organizations.models import Organization


class Facility(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="facilities"
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_facilities"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Building(BaseModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="buildings")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "cymed_facility_buildings"


class Floor(BaseModel):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="floors")
    name = models.CharField(max_length=100)  # e.g., "Ground Floor", "1st Floor"
    level = models.IntegerField()  # e.g., 0, 1, 2, -1 for basement

    class Meta:
        db_table = "cymed_facility_floors"


class Department(BaseModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, db_index=True)

    class Meta:
        db_table = "cymed_facility_departments"


class Ward(BaseModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="wards")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "cymed_facility_wards"


class Room(BaseModel):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=50)
    room_type = models.CharField(
        max_length=50,
        choices=[
            ("icu", "Intensive Care Unit"),
            ("operating", "Operating Room"),
            ("recovery", "Recovery Room"),
            ("standard", "Standard Patient Room"),
            ("exam", "Examination Room"),
        ],
        default="standard",
    )

    class Meta:
        db_table = "cymed_facility_rooms"


class Bed(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.CharField(max_length=50)
    status = models.CharField(
        max_length=30,
        choices=[
            ("available", "Available"),
            ("occupied", "Occupied"),
            ("maintenance", "Maintenance"),
            ("reserved", "Reserved"),
        ],
        default="available",
    )

    class Meta:
        db_table = "cymed_facility_beds"


class ResourceLocation(BaseModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="resources")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    resource_type = models.CharField(max_length=100)  # e.g., "ventilator", "ultrasound"
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_facility_resource_locations"
