import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProviderResultView",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                (
                    "result_type",
                    models.CharField(
                        choices=[
                            ("laboratory", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("pathology", "Pathology"),
                            ("microbiology", "Microbiology"),
                            ("cardiology", "Cardiology"),
                            ("pulmonary", "Pulmonary"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("result_source_id", models.UUIDField()),
                ("result_source_type", models.CharField(max_length=50)),
                ("result_name", models.CharField(max_length=255)),
                ("result_date", models.DateField(db_index=True)),
                (
                    "result_status",
                    models.CharField(
                        choices=[
                            ("preliminary", "Preliminary"),
                            ("final", "Final"),
                            ("corrected", "Corrected"),
                            ("amended", "Amended"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="final",
                        max_length=20,
                    ),
                ),
                ("is_critical", models.BooleanField(default=False)),
                ("is_reviewed", models.BooleanField(default=False)),
                ("reviewed_by_provider_id", models.UUIDField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("is_acknowledged", models.BooleanField(default=False)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("ordering_provider_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("fhir_diagnostic_report_id", models.CharField(blank=True, max_length=255)),
                ("result_summary", models.TextField(blank=True)),
                ("loinc_code", models.CharField(blank=True, max_length=50)),
            ],
            options={"db_table": "cymed_prov_results"},
        ),
        migrations.CreateModel(
            name="ResultTrend",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("test_code", models.CharField(db_index=True, max_length=100)),
                ("test_name", models.CharField(max_length=255)),
                ("loinc_code", models.CharField(blank=True, max_length=50)),
                ("unit", models.CharField(blank=True, max_length=50)),
                ("datapoints", models.JSONField(default=list)),
                (
                    "reference_range_low",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
                ),
                (
                    "reference_range_high",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
                ),
            ],
            options={"db_table": "cymed_prov_result_trends"},
        ),
        migrations.CreateModel(
            name="CriticalResultAlert",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="critical_alerts",
                        to="cymed_provider_results.providerresultview",
                    ),
                ),
                ("patient_id", models.UUIDField(db_index=True)),
                ("alerted_provider_id", models.UUIDField(db_index=True)),
                ("alerted_provider_name", models.CharField(max_length=255)),
                (
                    "alert_type",
                    models.CharField(
                        choices=[
                            ("critical_value", "Critical Value"),
                            ("panic_value", "Panic Value"),
                            ("abnormal_flag", "Abnormal Flag"),
                            ("delta_check", "Delta Check"),
                        ],
                        max_length=30,
                    ),
                ),
                ("result_value", models.CharField(max_length=255)),
                ("normal_range", models.CharField(blank=True, max_length=255)),
                ("clinical_significance", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("acknowledged", "Acknowledged"),
                            ("escalated", "Escalated"),
                            ("resolved", "Resolved"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("escalated_at", models.DateTimeField(blank=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("action_taken", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_prov_critical_alerts"},
        ),
        migrations.CreateModel(
            name="ResultAcknowledgement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="acknowledgements",
                        to="cymed_provider_results.providerresultview",
                    ),
                ),
                ("provider_id", models.UUIDField()),
                ("provider_name", models.CharField(max_length=255)),
                ("provider_type", models.CharField(max_length=100)),
                (
                    "action_taken",
                    models.CharField(
                        choices=[
                            ("noted", "Noted"),
                            ("ordered_follow_up", "Ordered Follow-Up"),
                            ("contacted_patient", "Contacted Patient"),
                            ("consulted_specialist", "Consulted Specialist"),
                            ("no_action_required", "No Action Required"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("action_notes", models.TextField(blank=True)),
                ("follow_up_date", models.DateField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_result_acks"},
        ),
        migrations.AddIndex(
            model_name="providerresultview",
            index=models.Index(
                fields=["tenant_id", "patient_id", "result_type"],
                name="cymed_prov_res_tid_pid_type_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="providerresultview",
            index=models.Index(
                fields=["tenant_id", "ordering_provider_id", "is_reviewed"],
                name="cymed_prov_res_tid_opid_rev_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="resulttrend",
            unique_together={("tenant_id", "patient_id", "test_code")},
        ),
    ]
