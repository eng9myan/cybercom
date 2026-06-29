import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Cohort",
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
                    "cohort_type",
                    models.CharField(
                        choices=[
                            ("study", "Study"),
                            ("quality", "Quality"),
                            ("population", "Population"),
                            ("intervention", "Intervention"),
                            ("control", "Control"),
                            ("registry", "Registry"),
                            ("benchmark", "Benchmark"),
                        ],
                        max_length=20,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("inclusion_criteria", models.JSONField(default=dict)),
                ("exclusion_criteria", models.JSONField(default=dict)),
                ("created_by_user_id", models.UUIDField()),
                ("patient_count", models.PositiveIntegerField(default=0)),
                ("is_dynamic", models.BooleanField(default=True)),
                ("last_updated_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_ph_coh_cohorts",
            },
        ),
        migrations.CreateModel(
            name="CohortMember",
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
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("removed_at", models.DateTimeField(blank=True, null=True)),
                ("removal_reason", models.CharField(blank=True, max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "cohort",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members",
                        to="cymed_ph_cohorts.cohort",
                    ),
                ),
            ],
            options={
                "db_table": "cymed_ph_coh_members",
                "unique_together": {("tenant_id", "cohort", "patient_id")},
            },
        ),
        migrations.CreateModel(
            name="CohortOutcome",
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
                ("outcome_name", models.CharField(max_length=200)),
                (
                    "outcome_type",
                    models.CharField(
                        choices=[
                            ("clinical", "Clinical"),
                            ("quality", "Quality"),
                            ("cost", "Cost"),
                            ("utilization", "Utilization"),
                            ("satisfaction", "Satisfaction"),
                        ],
                        max_length=30,
                    ),
                ),
                ("measurement_date", models.DateField()),
                ("value", models.CharField(blank=True, max_length=200)),
                ("unit", models.CharField(blank=True, max_length=50)),
                ("icd11_code", models.CharField(blank=True, max_length=20)),
                ("notes", models.TextField(blank=True)),
                (
                    "cohort",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outcomes",
                        to="cymed_ph_cohorts.cohort",
                    ),
                ),
            ],
            options={
                "db_table": "cymed_ph_coh_outcomes",
            },
        ),
        migrations.CreateModel(
            name="CohortAnalysis",
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
                    "analysis_type",
                    models.CharField(
                        choices=[
                            ("descriptive", "Descriptive"),
                            ("comparative", "Comparative"),
                            ("trend", "Trend"),
                            ("outcome", "Outcome"),
                            ("predictive", "Predictive"),
                            ("survival", "Survival"),
                        ],
                        max_length=30,
                    ),
                ),
                ("analysis_name", models.CharField(max_length=200)),
                ("analysis_date", models.DateField()),
                ("results", models.JSONField(default=dict)),
                ("performed_by_user_id", models.UUIDField(blank=True, null=True)),
                ("is_ai_generated", models.BooleanField(default=False)),
                ("is_advisory_only", models.BooleanField(default=True, editable=False)),
                ("summary", models.TextField(blank=True)),
                (
                    "cohort",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="analyses",
                        to="cymed_ph_cohorts.cohort",
                    ),
                ),
            ],
            options={
                "db_table": "cymed_ph_coh_analyses",
            },
        ),
    ]
