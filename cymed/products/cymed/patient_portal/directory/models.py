from django.db import models

from platform.common.models import BaseModel

NETWORK_PROVIDER_TYPE_CHOICES = [
    ("hospital", "Hospital"),
    ("clinic", "Clinic"),
    ("laboratory", "Laboratory"),
    ("imaging_center", "Imaging Center"),
    ("pharmacy", "Pharmacy"),
]


class HospitalListing(BaseModel):
    hospital_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(max_length=2000, blank=True)
    cover_image_url = models.URLField(max_length=2000, blank=True)
    description = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=3)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(max_length=500, blank=True)
    emergency_number = models.CharField(max_length=50, blank=True)
    bed_count = models.PositiveSmallIntegerField(default=0)
    accreditations = models.JSONField(default=list)
    specialties = models.JSONField(default=list)
    services = models.JSONField(default=list)
    departments = models.JSONField(default=list)
    operating_hours = models.JSONField(default=dict)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    accepts_insurance = models.BooleanField(default=True)
    accepts_walk_in = models.BooleanField(default=False)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_dir_hospitals"
        indexes = [
            models.Index(fields=["tenant_id", "city", "is_published"]),
            models.Index(fields=["is_featured", "is_published"]),
        ]

    def __str__(self):
        return self.name


class ClinicListing(BaseModel):
    clinic_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(max_length=2000, blank=True)
    description = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=3)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    specialties = models.JSONField(default=list)
    primary_specialty = models.CharField(max_length=100, blank=True)
    services = models.JSONField(default=list)
    operating_hours = models.JSONField(default=dict)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    accepts_insurance = models.BooleanField(default=True)
    accepts_walk_in = models.BooleanField(default=False)
    telemedicine_available = models.BooleanField(default=False)
    home_visit_available = models.BooleanField(default=False)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_dir_clinics"
        indexes = [
            models.Index(fields=["tenant_id", "city", "primary_specialty", "is_published"]),
            models.Index(fields=["is_featured"]),
        ]

    def __str__(self):
        return self.name


class ClinicSpecialty(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100, blank=True)
    icon_url = models.URLField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    snomed_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cymed_dir_clinic_specialties"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class LaboratoryListing(BaseModel):
    lab_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(max_length=2000, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=3)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    services = models.JSONField(default=list)
    test_panels = models.JSONField(default=list)
    branches = models.JSONField(default=list)
    accreditations = models.JSONField(default=list)
    turnaround_times = models.JSONField(default=dict)
    home_collection = models.BooleanField(default=False)
    operating_hours = models.JSONField(default=dict)
    is_published = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_dir_laboratories"

    def __str__(self):
        return self.name


class ImagingCenterListing(BaseModel):
    center_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(max_length=2000, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=3)
    phone = models.CharField(max_length=50, blank=True)
    modalities = models.JSONField(default=list)
    radiologists = models.JSONField(default=list)
    locations = models.JSONField(default=list)
    operating_hours = models.JSONField(default=dict)
    is_published = models.BooleanField(default=True)
    accreditations = models.JSONField(default=list)

    class Meta:
        db_table = "cymed_dir_imaging_centers"

    def __str__(self):
        return self.name


class PharmacyListing(BaseModel):
    pharmacy_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(max_length=2000, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=3)
    phone = models.CharField(max_length=50, blank=True)
    branches = models.JSONField(default=list)
    operating_hours = models.JSONField(default=dict)
    services = models.JSONField(default=list)
    is_published = models.BooleanField(default=True)
    is_24_hours = models.BooleanField(default=False)
    home_delivery = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_dir_pharmacies"

    def __str__(self):
        return self.name


class ProviderReview(BaseModel):
    reviewer_account_id = models.UUIDField(db_index=True)
    provider_type = models.CharField(
        max_length=30,
        choices=NETWORK_PROVIDER_TYPE_CHOICES,
    )
    provider_listing_id = models.UUIDField(db_index=True)
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200, blank=True)
    review_text = models.TextField(blank=True)
    visit_date = models.DateField(null=True, blank=True)
    is_verified_visit = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    moderated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_dir_reviews"
        indexes = [
            models.Index(fields=["provider_type", "provider_listing_id", "is_published"]),
        ]

    def __str__(self):
        return f"Review by {self.reviewer_account_id} - {self.provider_type} ({self.rating}/5)"
