import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LabResultView",
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
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("cymed_lab_result_id", models.UUIDField(db_index=True)),
                ("lab_id", models.UUIDField(db_index=True)),
                ("lab_name", models.CharField(max_length=255)),
                ("order_number", models.CharField(blank=True, max_length=100)),
                ("test_name", models.CharField(max_length=500)),
                ("test_code", models.CharField(blank=True, max_length=100)),
                ("loinc_code", models.CharField(blank=True, max_length=20)),
                ("specimen_type", models.CharField(blank=True, max_length=100)),
                ("collected_at", models.DateTimeField(blank=True, null=True)),
                ("resulted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "result_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("partial", "Partial"),
                            ("final", "Final"),
                            ("corrected", "Corrected"),
                            ("amended", "Amended"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("result_summary", models.TextField(blank=True)),
                ("is_critical", models.BooleanField(default=False)),
                ("is_viewed", models.BooleanField(default=False)),
                ("viewed_at", models.DateTimeField(blank=True, null=True)),
                ("pdf_url", models.URLField(blank=True, max_length=2000)),
                (
                    "fhir_diagnostic_report_id",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
            ],
            options={
                "db_table": "cymed_portal_lab_results",
            },
        ),
        migrations.CreateModel(
            name="LabResultTrend",
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
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("test_code", models.CharField(db_index=True, max_length=100)),
                ("test_name", models.CharField(max_length=500)),
                ("loinc_code", models.CharField(blank=True, max_length=20)),
                ("datapoints", models.JSONField(default=list)),
                ("unit", models.CharField(blank=True, max_length=50)),
                (
                    "reference_range_low",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
                ),
                (
                    "reference_range_high",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
                ),
                ("last_updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "cymed_portal_lab_trends",
            },
        ),
        migrations.CreateModel(
            name="CriticalResultAcknowledgement",
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
                (
                    "lab_result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="acknowledgements",
                        to="cymed_portal_laboratory_results.labresultview",
                    ),
                ),
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("acknowledged_at", models.DateTimeField(auto_now_add=True)),
                (
                    "action_taken",
                    models.CharField(
                        choices=[
                            ("contacted_provider", "Contacted Provider"),
                            ("scheduled_appointment", "Scheduled Appointment"),
                            ("went_to_er", "Went to ER"),
                            ("no_action", "No Action"),
                            ("other", "Other"),
                        ],
                        default="no_action",
                        max_length=30,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("notified_provider_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_critical_ack",
            },
        ),
        migrations.CreateModel(
            name="LabResultShareLink",
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
                (
                    "lab_result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="share_links",
                        to="cymed_portal_laboratory_results.labresultview",
                    ),
                ),
                ("account_id", models.UUIDField(db_index=True)),
                ("share_token", models.CharField(db_index=True, max_length=255, unique=True)),
                ("shared_with_name", models.CharField(blank=True, max_length=255)),
                ("shared_with_email", models.EmailField(blank=True)),
                ("valid_until", models.DateTimeField()),
                ("access_count", models.PositiveIntegerField(default=0)),
                ("is_revoked", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "cymed_portal_lab_share_links",
            },
        ),
        migrations.AddIndex(
            model_name="labresultview",
            index=models.Index(
                fields=["account_id", "result_status", "resulted_at"],
                name="lab_results_acct_status_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="labresultview",
            index=models.Index(
                fields=["patient_id", "is_critical"],
                name="lab_results_patient_critical_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="labresulttrend",
            unique_together={("tenant_id", "patient_id", "test_code")},
        ),
    ]
