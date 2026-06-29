import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProviderProductivitySnapshot",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("provider_type", models.CharField(max_length=100)),
                ("snapshot_date", models.DateField(db_index=True)),
                (
                    "snapshot_period",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        default="daily",
                        max_length=20,
                    ),
                ),
                ("patients_seen", models.PositiveIntegerField(default=0)),
                ("notes_completed", models.PositiveIntegerField(default=0)),
                ("notes_pending", models.PositiveIntegerField(default=0)),
                ("orders_placed", models.PositiveIntegerField(default=0)),
                ("results_reviewed", models.PositiveIntegerField(default=0)),
                ("tasks_completed", models.PositiveIntegerField(default=0)),
                ("tasks_pending", models.PositiveIntegerField(default=0)),
                ("messages_sent", models.PositiveIntegerField(default=0)),
                ("telemedicine_sessions", models.PositiveIntegerField(default=0)),
                (
                    "avg_documentation_time_minutes",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        max_digits=6,
                        null=True,
                    ),
                ),
                (
                    "avg_result_review_minutes",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        max_digits=6,
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "cymed_prov_productivity_snapshots",
            },
        ),
        migrations.CreateModel(
            name="ClinicalQualityMetric",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("documentation_completion", "Documentation Completion"),
                            ("result_acknowledgement", "Result Acknowledgement"),
                            ("medication_error_rate", "Medication Error Rate"),
                            ("hand_hygiene_compliance", "Hand Hygiene Compliance"),
                            ("patient_satisfaction", "Patient Satisfaction"),
                            ("readmission_rate", "Readmission Rate"),
                            ("mortality_rate", "Mortality Rate"),
                            ("infection_rate", "Infection Rate"),
                            ("order_accuracy", "Order Accuracy"),
                            ("care_gap_closure", "Care Gap Closure"),
                        ],
                        max_length=50,
                    ),
                ),
                ("metric_name", models.CharField(max_length=255)),
                ("measured_at", models.DateField(db_index=True)),
                (
                    "scope_type",
                    models.CharField(
                        choices=[
                            ("provider", "Provider"),
                            ("unit", "Unit"),
                            ("department", "Department"),
                            ("facility", "Facility"),
                        ],
                        max_length=20,
                    ),
                ),
                ("scope_id", models.UUIDField(db_index=True)),
                ("scope_name", models.CharField(max_length=255)),
                (
                    "numerator",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "denominator",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "rate",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=6,
                        null=True,
                    ),
                ),
                (
                    "target_rate",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=6,
                        null=True,
                    ),
                ),
                (
                    "benchmark_rate",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=6,
                        null=True,
                    ),
                ),
                ("meets_target", models.BooleanField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_prov_quality_metrics",
            },
        ),
        migrations.CreateModel(
            name="WorkforceDashboardSnapshot",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("unit_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("unit_name", models.CharField(blank=True, max_length=255)),
                ("department", models.CharField(blank=True, max_length=255)),
                ("snapshot_date", models.DateField(db_index=True)),
                ("total_providers", models.PositiveIntegerField(default=0)),
                ("providers_on_duty", models.PositiveIntegerField(default=0)),
                ("providers_on_leave", models.PositiveIntegerField(default=0)),
                ("providers_on_call", models.PositiveIntegerField(default=0)),
                ("unfilled_shifts", models.PositiveIntegerField(default=0)),
                ("credential_expiry_alerts", models.PositiveIntegerField(default=0)),
                ("pending_leave_requests", models.PositiveIntegerField(default=0)),
                ("open_tasks", models.PositiveIntegerField(default=0)),
                ("critical_alerts_pending", models.PositiveIntegerField(default=0)),
                ("patient_census", models.PositiveIntegerField(default=0)),
                (
                    "staff_patient_ratio",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=5,
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "cymed_prov_workforce_snapshots",
            },
        ),
        migrations.CreateModel(
            name="ProviderAIInsight",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(blank=True, db_index=True, null=True)),
                (
                    "insight_type",
                    models.CharField(
                        choices=[
                            ("care_gap", "Care Gap"),
                            ("risk_stratification", "Risk Stratification"),
                            ("documentation_suggestion", "Documentation Suggestion"),
                            ("coding_suggestion", "Coding Suggestion"),
                            ("order_suggestion", "Order Suggestion"),
                            ("clinical_alert", "Clinical Alert"),
                            ("care_coordination", "Care Coordination"),
                        ],
                        max_length=50,
                    ),
                ),
                ("insight_title", models.CharField(max_length=255)),
                ("insight_body", models.TextField()),
                (
                    "confidence_score",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=4,
                        null=True,
                    ),
                ),
                ("source_data", models.JSONField(default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending_review", "Pending Review"),
                            ("acknowledged", "Acknowledged"),
                            ("acted_upon", "Acted Upon"),
                            ("dismissed", "Dismissed"),
                        ],
                        default="pending_review",
                        max_length=20,
                    ),
                ),
                ("acknowledged_by", models.UUIDField(blank=True, null=True)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("action_taken", models.TextField(blank=True)),
                (
                    "is_advisory_only",
                    models.BooleanField(default=True, editable=False),
                ),
            ],
            options={
                "db_table": "cymed_prov_ai_insights",
            },
        ),
        migrations.CreateModel(
            name="ExecutiveDashboardMetric",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "metric_category",
                    models.CharField(
                        choices=[
                            ("clinical_quality", "Clinical Quality"),
                            ("workforce", "Workforce"),
                            ("financial", "Financial"),
                            ("operational", "Operational"),
                            ("patient_safety", "Patient Safety"),
                            ("research", "Research"),
                        ],
                        max_length=30,
                    ),
                ),
                ("metric_name", models.CharField(max_length=255)),
                (
                    "metric_value",
                    models.DecimalField(decimal_places=2, max_digits=15),
                ),
                ("metric_unit", models.CharField(blank=True, max_length=50)),
                ("metric_date", models.DateField(db_index=True)),
                ("facility_id", models.UUIDField(blank=True, null=True)),
                ("department", models.CharField(blank=True, max_length=255)),
                (
                    "comparison_value",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=15,
                        null=True,
                    ),
                ),
                (
                    "trend_direction",
                    models.CharField(
                        choices=[
                            ("improving", "Improving"),
                            ("stable", "Stable"),
                            ("declining", "Declining"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                (
                    "alert_threshold",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=15,
                        null=True,
                    ),
                ),
                ("is_above_threshold", models.BooleanField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_prov_exec_metrics",
            },
        ),
        # unique_together constraints
        migrations.AlterUniqueTogether(
            name="providerproductivitysnapshot",
            unique_together={("tenant_id", "provider_id", "snapshot_date", "snapshot_period")},
        ),
        migrations.AlterUniqueTogether(
            name="workforcedashboardsnapshot",
            unique_together={("tenant_id", "unit_id", "snapshot_date")},
        ),
        # Indexes
        migrations.AddIndex(
            model_name="providerproductivitysnapshot",
            index=models.Index(
                fields=["tenant_id", "provider_id", "snapshot_date"],
                name="cymed_prov_prod_snap_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicalqualitymetric",
            index=models.Index(
                fields=["tenant_id", "scope_id", "metric_type", "measured_at"],
                name="cymed_prov_qual_metric_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="provideraiinsight",
            index=models.Index(
                fields=["tenant_id", "provider_id", "insight_type", "status"],
                name="cymed_prov_ai_insight_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="executivedashboardmetric",
            index=models.Index(
                fields=["tenant_id", "metric_category", "metric_date"],
                name="cymed_prov_exec_metric_idx",
            ),
        ),
    ]
