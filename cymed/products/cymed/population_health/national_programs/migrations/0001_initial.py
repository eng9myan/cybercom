import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HealthProgram",
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
                ("program_code", models.CharField(max_length=50, unique=True)),
                ("program_name", models.CharField(max_length=200)),
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
                            ("cardiovascular", "Cardiovascular"),
                            ("elderly_care", "Elderly Care"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("governing_authority", models.CharField(blank=True, max_length=200)),
                ("description", models.TextField(blank=True)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("target_population_description", models.TextField(blank=True)),
                ("target_age_min", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("target_age_max", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("target_population_size", models.PositiveIntegerField(default=0)),
                ("enrolled_count", models.PositiveIntegerField(default=0)),
                ("completion_count", models.PositiveIntegerField(default=0)),
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
                ("related_icd11_codes", models.JSONField(default=list)),
                ("fhir_care_plan_id", models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={"db_table": "cymed_ph_prog_programs"},
        ),
        migrations.CreateModel(
            name="ProgramEnrollment",
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
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="enrollments",
                        to="cymed_ph_national_programs.healthprogram",
                    ),
                ),
                ("patient_id", models.UUIDField(db_index=True)),
                ("enrollment_date", models.DateField()),
                ("enrolled_by_user_id", models.UUIDField(blank=True, null=True)),
                ("enrollment_facility_id", models.UUIDField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("withdrawn", "Withdrawn"),
                            ("transferred", "Transferred"),
                            ("lost_to_followup", "Lost to Follow-up"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("expected_completion_date", models.DateField(blank=True, null=True)),
                ("actual_completion_date", models.DateField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_ph_prog_enrollments",
                "unique_together": {("tenant_id", "program", "patient_id")},
            },
        ),
        migrations.CreateModel(
            name="ProgramOutcome",
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
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="outcomes",
                        to="cymed_ph_national_programs.healthprogram",
                    ),
                ),
                ("patient_id", models.UUIDField(db_index=True)),
                (
                    "outcome_type",
                    models.CharField(
                        choices=[
                            ("screening_complete", "Screening Complete"),
                            ("vaccination_complete", "Vaccination Complete"),
                            ("goal_achieved", "Goal Achieved"),
                            ("condition_improved", "Condition Improved"),
                            ("hospitalization_avoided", "Hospitalisation Avoided"),
                            ("complication_prevented", "Complication Prevented"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("outcome_date", models.DateField()),
                ("outcome_value", models.CharField(blank=True, max_length=200)),
                ("outcome_notes", models.TextField(blank=True)),
                ("recording_provider_id", models.UUIDField(blank=True, null=True)),
                ("icd11_code", models.CharField(blank=True, max_length=20)),
                ("loinc_code", models.CharField(blank=True, max_length=30)),
            ],
            options={"db_table": "cymed_ph_prog_outcomes"},
        ),
        migrations.CreateModel(
            name="ProgramMetric",
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
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="metrics",
                        to="cymed_ph_national_programs.healthprogram",
                    ),
                ),
                ("metric_name", models.CharField(max_length=200)),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("coverage", "Coverage"),
                            ("adherence", "Adherence"),
                            ("outcome", "Outcome"),
                            ("efficiency", "Efficiency"),
                            ("cost_effectiveness", "Cost-Effectiveness"),
                            ("patient_satisfaction", "Patient Satisfaction"),
                        ],
                        max_length=20,
                    ),
                ),
                ("metric_date", models.DateField()),
                (
                    "target_value",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                ("actual_value", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("unit", models.CharField(blank=True, max_length=50)),
                ("meets_target", models.BooleanField(default=False)),
                ("calculation_notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_ph_prog_metrics",
                "unique_together": {("tenant_id", "program", "metric_name", "metric_date")},
            },
        ),
    ]
