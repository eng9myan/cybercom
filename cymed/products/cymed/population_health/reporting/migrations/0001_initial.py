import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NationalReport",
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
                ("report_name", models.CharField(max_length=200)),
                (
                    "report_type",
                    models.CharField(
                        choices=[
                            ("annual_health", "Annual Health"),
                            ("disease_surveillance", "Disease Surveillance"),
                            ("registry_report", "Registry Report"),
                            ("vaccination_coverage", "Vaccination Coverage"),
                            ("quality_report", "Quality Report"),
                            ("outbreak_report", "Outbreak Report"),
                            ("program_report", "Program Report"),
                            ("ministry_report", "Ministry Report"),
                            ("who_report", "WHO Report"),
                        ],
                        max_length=30,
                    ),
                ),
                ("reporting_period_start", models.DateField()),
                ("reporting_period_end", models.DateField()),
                ("report_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("in_review", "In Review"),
                            ("approved", "Approved"),
                            ("submitted", "Submitted"),
                            ("published", "Published"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("generated_by_user_id", models.UUIDField(blank=True, null=True)),
                ("approved_by_user_id", models.UUIDField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("submitted_to_authority", models.CharField(blank=True, max_length=200)),
                ("content", models.JSONField(default=dict)),
                ("fhir_measure_report_id", models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={"db_table": "cymed_ph_rep_reports"},
        ),
        migrations.CreateModel(
            name="ReportTemplate",
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
                ("template_name", models.CharField(max_length=200)),
                (
                    "report_type",
                    models.CharField(
                        choices=[
                            ("annual_health", "Annual Health"),
                            ("disease_surveillance", "Disease Surveillance"),
                            ("registry_report", "Registry Report"),
                            ("vaccination_coverage", "Vaccination Coverage"),
                            ("quality_report", "Quality Report"),
                            ("outbreak_report", "Outbreak Report"),
                            ("program_report", "Program Report"),
                            ("ministry_report", "Ministry Report"),
                            ("who_report", "WHO Report"),
                        ],
                        max_length=30,
                    ),
                ),
                ("template_definition", models.JSONField(default=dict)),
                ("is_national_standard", models.BooleanField(default=False)),
                ("governing_standard", models.CharField(blank=True, max_length=200)),
                ("version", models.CharField(default="1.0", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_ph_rep_templates"},
        ),
        migrations.CreateModel(
            name="GovernmentSubmission",
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
                    "national_report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="submissions",
                        to="cymed_ph_reporting.nationalreport",
                    ),
                ),
                ("submission_date", models.DateTimeField()),
                ("submitted_by_user_id", models.UUIDField()),
                (
                    "submission_method",
                    models.CharField(
                        choices=[
                            ("electronic", "Electronic"),
                            ("api", "API"),
                            ("email", "Email"),
                            ("portal", "Portal"),
                            ("manual", "Manual"),
                        ],
                        default="electronic",
                        max_length=20,
                    ),
                ),
                ("submission_endpoint", models.CharField(blank=True, max_length=500)),
                ("reference_number", models.CharField(blank=True, max_length=200, null=True)),
                ("acknowledgement_received", models.BooleanField(default=False)),
                ("acknowledgement_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("submitted", "Submitted"),
                            ("acknowledged", "Acknowledged"),
                            ("rejected", "Rejected"),
                            ("accepted", "Accepted"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("rejection_reason", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_ph_rep_submissions"},
        ),
        migrations.CreateModel(
            name="ReportSchedule",
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
                    "report_type",
                    models.CharField(
                        choices=[
                            ("annual_health", "Annual Health"),
                            ("disease_surveillance", "Disease Surveillance"),
                            ("registry_report", "Registry Report"),
                            ("vaccination_coverage", "Vaccination Coverage"),
                            ("quality_report", "Quality Report"),
                            ("outbreak_report", "Outbreak Report"),
                            ("program_report", "Program Report"),
                            ("ministry_report", "Ministry Report"),
                            ("who_report", "WHO Report"),
                        ],
                        max_length=30,
                    ),
                ),
                ("schedule_name", models.CharField(max_length=200)),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                            ("quarterly", "Quarterly"),
                            ("annual", "Annual"),
                            ("as_needed", "As Needed"),
                        ],
                        max_length=20,
                    ),
                ),
                ("next_due_date", models.DateField()),
                ("responsible_user_id", models.UUIDField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("last_generated_at", models.DateTimeField(blank=True, null=True)),
                ("auto_generate", models.BooleanField(default=False)),
                ("auto_submit", models.BooleanField(default=False)),
                ("submission_authority", models.CharField(blank=True, max_length=200)),
            ],
            options={"db_table": "cymed_ph_rep_schedules"},
        ),
    ]
