import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PopulationGroup",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("name", models.CharField(max_length=200)),
                (
                    "group_type",
                    models.CharField(
                        choices=[
                            ("geographic", "Geographic"),
                            ("demographic", "Demographic"),
                            ("clinical", "Clinical"),
                            ("risk", "Risk"),
                            ("program", "Program"),
                            ("chronic_disease", "Chronic Disease"),
                            ("insurance", "Insurance"),
                        ],
                        max_length=30,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("criteria", models.JSONField(default=dict)),
                ("estimated_size", models.PositiveIntegerField(default=0)),
                ("geographic_scope", models.CharField(blank=True, max_length=100)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_ph_pop_groups"},
        ),
        migrations.CreateModel(
            name="PopulationSegment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "population_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="segments",
                        to="cymed_ph_public_health.populationgroup",
                    ),
                ),
                ("segment_name", models.CharField(max_length=200)),
                ("segment_criteria", models.JSONField(default=dict)),
                ("patient_count", models.PositiveIntegerField(default=0)),
                ("last_calculated_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_ph_pop_segments"},
        ),
        migrations.CreateModel(
            name="HealthRisk",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                (
                    "risk_type",
                    models.CharField(
                        choices=[
                            ("cardiovascular", "Cardiovascular"),
                            ("diabetes", "Diabetes"),
                            ("cancer", "Cancer"),
                            ("respiratory", "Respiratory"),
                            ("mental_health", "Mental Health"),
                            ("falls", "Falls"),
                            ("readmission", "Readmission"),
                            ("mortality", "Mortality"),
                            ("high_cost", "High Cost"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "risk_level",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("moderate", "Moderate"),
                            ("high", "High"),
                            ("very_high", "Very High"),
                            ("critical", "Critical"),
                        ],
                        default="low",
                        max_length=15,
                    ),
                ),
                (
                    "risk_score",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
                ),
                ("icd11_codes", models.JSONField(default=list)),
                ("assessment_date", models.DateField()),
                ("next_assessment_date", models.DateField(blank=True, null=True)),
                ("assessed_by_user_id", models.UUIDField(blank=True, null=True)),
                ("is_ai_generated", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "cymed_ph_pop_health_risks",
                "ordering": ["-assessment_date"],
            },
        ),
        migrations.CreateModel(
            name="HealthGoal",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                (
                    "goal_type",
                    models.CharField(
                        choices=[
                            ("weight_loss", "Weight Loss"),
                            ("bp_control", "Blood Pressure Control"),
                            ("glucose_control", "Glucose Control"),
                            ("smoking_cessation", "Smoking Cessation"),
                            ("exercise", "Exercise"),
                            ("medication_adherence", "Medication Adherence"),
                            ("vaccination", "Vaccination"),
                            ("screening", "Screening"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("target_value", models.CharField(blank=True, max_length=100)),
                ("current_value", models.CharField(blank=True, max_length=100)),
                ("unit", models.CharField(blank=True, max_length=30)),
                ("start_date", models.DateField()),
                ("target_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("achieved", "Achieved"),
                            ("not_achieved", "Not Achieved"),
                            ("abandoned", "Abandoned"),
                            ("on_hold", "On Hold"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("assigned_provider_id", models.UUIDField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_ph_pop_health_goals"},
        ),
        migrations.CreateModel(
            name="PopulationProgram",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("name", models.CharField(max_length=200)),
                (
                    "program_type",
                    models.CharField(
                        choices=[
                            ("vaccination", "Vaccination"),
                            ("screening", "Screening"),
                            ("chronic_disease", "Chronic Disease"),
                            ("maternal", "Maternal"),
                            ("child_health", "Child Health"),
                            ("mental_health", "Mental Health"),
                            ("cancer", "Cancer"),
                            ("nutrition", "Nutrition"),
                            ("smoking_cessation", "Smoking Cessation"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("target_population_description", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planning", "Planning"),
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("suspended", "Suspended"),
                        ],
                        default="planning",
                        max_length=20,
                    ),
                ),
                ("program_manager_id", models.UUIDField(blank=True, null=True)),
                ("target_count", models.PositiveIntegerField(default=0)),
                ("enrolled_count", models.PositiveIntegerField(default=0)),
            ],
            options={"db_table": "cymed_ph_pop_programs"},
        ),
        migrations.CreateModel(
            name="NationalProvider",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("national_provider_number", models.CharField(max_length=100, unique=True)),
                (
                    "provider_type",
                    models.CharField(
                        choices=[
                            ("physician", "Physician"),
                            ("specialist", "Specialist"),
                            ("nurse", "Nurse"),
                            ("pharmacist", "Pharmacist"),
                            ("therapist", "Therapist"),
                            ("lab_technician", "Lab Technician"),
                            ("radiologist", "Radiologist"),
                            ("dentist", "Dentist"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("specialty", models.CharField(blank=True, max_length=100)),
                ("registration_date", models.DateField()),
                (
                    "registration_status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("suspended", "Suspended"),
                            ("revoked", "Revoked"),
                            ("expired", "Expired"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("primary_facility_id", models.UUIDField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_ph_pop_national_providers"},
        ),
        migrations.CreateModel(
            name="ProviderCredential",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "national_provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credentials",
                        to="cymed_ph_public_health.nationalprovider",
                    ),
                ),
                (
                    "credential_type",
                    models.CharField(
                        choices=[
                            ("medical_license", "Medical License"),
                            ("specialty_board", "Specialty Board"),
                            ("cme", "CME"),
                            ("bls", "BLS"),
                            ("acls", "ACLS"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                ("credential_number", models.CharField(max_length=100)),
                ("issuing_authority", models.CharField(max_length=200)),
                ("issue_date", models.DateField()),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("is_verified", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_ph_pop_provider_credentials"},
        ),
        migrations.CreateModel(
            name="NationalFacility",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("facility_id", models.UUIDField(db_index=True)),
                ("national_facility_number", models.CharField(max_length=100, unique=True)),
                (
                    "facility_type",
                    models.CharField(
                        choices=[
                            ("hospital", "Hospital"),
                            ("clinic", "Clinic"),
                            ("pharmacy", "Pharmacy"),
                            ("laboratory", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("rehabilitation", "Rehabilitation"),
                            ("mental_health", "Mental Health"),
                            ("emergency", "Emergency"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("facility_name", models.CharField(max_length=200)),
                (
                    "license_status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("suspended", "Suspended"),
                            ("revoked", "Revoked"),
                            ("expired", "Expired"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("registration_date", models.DateField()),
                ("beds_count", models.PositiveIntegerField(blank=True, null=True)),
                ("is_teaching", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_ph_pop_national_facilities"},
        ),
        migrations.CreateModel(
            name="FacilityAccreditation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "national_facility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accreditations",
                        to="cymed_ph_public_health.nationalfacility",
                    ),
                ),
                ("accreditation_body", models.CharField(max_length=200)),
                ("accreditation_type", models.CharField(max_length=100)),
                ("award_date", models.DateField()),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("accreditation_level", models.CharField(blank=True, max_length=50)),
                ("is_current", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_ph_pop_facility_accreditations"},
        ),
    ]
