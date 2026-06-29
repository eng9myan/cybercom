import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HospitalListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("hospital_id", models.UUIDField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("name_ar", models.CharField(blank=True, max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("logo_url", models.URLField(blank=True, max_length=2000)),
                ("cover_image_url", models.URLField(blank=True, max_length=2000)),
                ("description", models.TextField(blank=True)),
                ("description_ar", models.TextField(blank=True)),
                ("address", models.CharField(max_length=500)),
                ("city", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=3)),
                (
                    "latitude",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
                ),
                (
                    "longitude",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
                ),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("website", models.URLField(blank=True, max_length=500)),
                ("emergency_number", models.CharField(blank=True, max_length=50)),
                ("bed_count", models.PositiveSmallIntegerField(default=0)),
                ("accreditations", models.JSONField(default=list)),
                ("specialties", models.JSONField(default=list)),
                ("services", models.JSONField(default=list)),
                ("departments", models.JSONField(default=list)),
                ("operating_hours", models.JSONField(default=dict)),
                ("is_published", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("accepts_insurance", models.BooleanField(default=True)),
                ("accepts_walk_in", models.BooleanField(default=False)),
                (
                    "rating_average",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=3),
                ),
                ("review_count", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "cymed_dir_hospitals",
            },
        ),
        migrations.AddIndex(
            model_name="hospitallisting",
            index=models.Index(
                fields=["tenant_id", "city", "is_published"],
                name="cymed_dir_hosp_tenant_city_pub_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hospitallisting",
            index=models.Index(
                fields=["is_featured", "is_published"], name="cymed_dir_hosp_featured_pub_idx"
            ),
        ),
        migrations.CreateModel(
            name="ClinicListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("clinic_id", models.UUIDField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("name_ar", models.CharField(blank=True, max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("logo_url", models.URLField(blank=True, max_length=2000)),
                ("description", models.TextField(blank=True)),
                ("description_ar", models.TextField(blank=True)),
                ("address", models.CharField(max_length=500)),
                ("city", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=3)),
                (
                    "latitude",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
                ),
                (
                    "longitude",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
                ),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("specialties", models.JSONField(default=list)),
                ("primary_specialty", models.CharField(blank=True, max_length=100)),
                ("services", models.JSONField(default=list)),
                ("operating_hours", models.JSONField(default=dict)),
                ("is_published", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("accepts_insurance", models.BooleanField(default=True)),
                ("accepts_walk_in", models.BooleanField(default=False)),
                ("telemedicine_available", models.BooleanField(default=False)),
                ("home_visit_available", models.BooleanField(default=False)),
                (
                    "rating_average",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=3),
                ),
                ("review_count", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "cymed_dir_clinics",
            },
        ),
        migrations.AddIndex(
            model_name="cliniclisting",
            index=models.Index(
                fields=["tenant_id", "city", "primary_specialty", "is_published"],
                name="cymed_dir_clinic_tenant_city_spec_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="cliniclisting",
            index=models.Index(fields=["is_featured"], name="cymed_dir_clinic_featured_idx"),
        ),
        migrations.CreateModel(
            name="ClinicSpecialty",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("name_ar", models.CharField(blank=True, max_length=100)),
                ("icon_url", models.URLField(blank=True, max_length=500)),
                ("description", models.TextField(blank=True)),
                ("snomed_code", models.CharField(blank=True, max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "db_table": "cymed_dir_clinic_specialties",
                "ordering": ["display_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="LaboratoryListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lab_id", models.UUIDField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("name_ar", models.CharField(blank=True, max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("logo_url", models.URLField(blank=True, max_length=2000)),
                ("description", models.TextField(blank=True)),
                ("address", models.CharField(max_length=500)),
                ("city", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=3)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("services", models.JSONField(default=list)),
                ("test_panels", models.JSONField(default=list)),
                ("branches", models.JSONField(default=list)),
                ("accreditations", models.JSONField(default=list)),
                ("turnaround_times", models.JSONField(default=dict)),
                ("home_collection", models.BooleanField(default=False)),
                ("operating_hours", models.JSONField(default=dict)),
                ("is_published", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_dir_laboratories",
            },
        ),
        migrations.CreateModel(
            name="ImagingCenterListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("center_id", models.UUIDField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("name_ar", models.CharField(blank=True, max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("logo_url", models.URLField(blank=True, max_length=2000)),
                ("description", models.TextField(blank=True)),
                ("address", models.CharField(max_length=500)),
                ("city", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=3)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("modalities", models.JSONField(default=list)),
                ("radiologists", models.JSONField(default=list)),
                ("locations", models.JSONField(default=list)),
                ("operating_hours", models.JSONField(default=dict)),
                ("is_published", models.BooleanField(default=True)),
                ("accreditations", models.JSONField(default=list)),
            ],
            options={
                "db_table": "cymed_dir_imaging_centers",
            },
        ),
        migrations.CreateModel(
            name="PharmacyListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("pharmacy_id", models.UUIDField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("name_ar", models.CharField(blank=True, max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("logo_url", models.URLField(blank=True, max_length=2000)),
                ("description", models.TextField(blank=True)),
                ("address", models.CharField(max_length=500)),
                ("city", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=3)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("branches", models.JSONField(default=list)),
                ("operating_hours", models.JSONField(default=dict)),
                ("services", models.JSONField(default=list)),
                ("is_published", models.BooleanField(default=True)),
                ("is_24_hours", models.BooleanField(default=False)),
                ("home_delivery", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "cymed_dir_pharmacies",
            },
        ),
        migrations.CreateModel(
            name="ProviderReview",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewer_account_id", models.UUIDField(db_index=True)),
                (
                    "provider_type",
                    models.CharField(
                        choices=[
                            ("hospital", "Hospital"),
                            ("clinic", "Clinic"),
                            ("laboratory", "Laboratory"),
                            ("imaging_center", "Imaging Center"),
                            ("pharmacy", "Pharmacy"),
                        ],
                        max_length=30,
                    ),
                ),
                ("provider_listing_id", models.UUIDField(db_index=True)),
                ("rating", models.PositiveSmallIntegerField()),
                ("title", models.CharField(blank=True, max_length=200)),
                ("review_text", models.TextField(blank=True)),
                ("visit_date", models.DateField(blank=True, null=True)),
                ("is_verified_visit", models.BooleanField(default=False)),
                ("is_published", models.BooleanField(default=False)),
                ("moderated_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_dir_reviews",
            },
        ),
        migrations.AddIndex(
            model_name="providerreview",
            index=models.Index(
                fields=["provider_type", "provider_listing_id", "is_published"],
                name="cymed_dir_rev_type_listing_pub_idx",
            ),
        ),
    ]
