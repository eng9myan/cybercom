import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RevenueDashboardSnapshot",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("snapshot_date", models.DateField()),
                ("snapshot_period", models.CharField(
                    max_length=10,
                    choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
                )),
                ("facility_id", models.UUIDField(null=True, blank=True)),
                ("gross_revenue", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("net_revenue", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("total_charges", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("total_collections", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("total_adjustments", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("outstanding_ar", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("days_in_ar", models.DecimalField(max_digits=8, decimal_places=2, default=0)),
                ("collection_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ("claim_acceptance_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ("denial_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
            ],
            options={
                "db_table": "cymed_rcm_ana_revenue_snapshots",
                "ordering": ["-snapshot_date", "snapshot_period"],
                "unique_together": {("tenant_id", "snapshot_date", "snapshot_period", "facility_id")},
            },
        ),
        migrations.CreateModel(
            name="ClaimMetricsSnapshot",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("snapshot_date", models.DateField()),
                ("snapshot_period", models.CharField(
                    max_length=10,
                    choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
                )),
                ("insurance_company_id", models.UUIDField(null=True, blank=True)),
                ("total_claims_submitted", models.PositiveIntegerField(default=0)),
                ("total_claims_paid", models.PositiveIntegerField(default=0)),
                ("total_claims_denied", models.PositiveIntegerField(default=0)),
                ("total_claims_pending", models.PositiveIntegerField(default=0)),
                ("total_billed", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("total_paid", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("total_denied_amount", models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ("average_days_to_payment", models.DecimalField(max_digits=8, decimal_places=2, default=0)),
                ("first_pass_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
            ],
            options={
                "db_table": "cymed_rcm_ana_claim_metrics",
                "ordering": ["-snapshot_date", "snapshot_period"],
                "unique_together": {("tenant_id", "snapshot_date", "snapshot_period", "insurance_company_id")},
            },
        ),
        migrations.CreateModel(
            name="DenialAnalyticsSnapshot",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("snapshot_date", models.DateField()),
                ("snapshot_period", models.CharField(
                    max_length=10,
                    choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
                )),
                ("denial_category", models.CharField(
                    max_length=30,
                    choices=[
                        ("eligibility", "Eligibility"),
                        ("authorization", "Authorization"),
                        ("medical_necessity", "Medical Necessity"),
                        ("coding", "Coding"),
                        ("documentation", "Documentation"),
                        ("duplicate", "Duplicate"),
                        ("timely_filing", "Timely Filing"),
                        ("network", "Network"),
                        ("other", "Other"),
                    ],
                )),
                ("total_denials", models.PositiveIntegerField(default=0)),
                ("total_denial_amount", models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ("appeals_filed", models.PositiveIntegerField(default=0)),
                ("appeals_won", models.PositiveIntegerField(default=0)),
                ("amount_recovered", models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ("appeal_success_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
            ],
            options={
                "db_table": "cymed_rcm_ana_denial_snapshots",
                "ordering": ["-snapshot_date", "snapshot_period", "denial_category"],
            },
        ),
        migrations.CreateModel(
            name="PayerPerformanceSnapshot",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("snapshot_date", models.DateField()),
                ("snapshot_period", models.CharField(
                    max_length=10,
                    choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
                )),
                ("insurance_company_id", models.UUIDField(db_index=True)),
                ("average_processing_days", models.DecimalField(max_digits=8, decimal_places=2, default=0)),
                ("payment_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ("denial_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ("auth_approval_rate", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ("avg_auth_processing_days", models.DecimalField(max_digits=8, decimal_places=2, default=0)),
                ("performance_score", models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)),
                ("trend_direction", models.CharField(
                    max_length=10,
                    choices=[
                        ("improving", "Improving"),
                        ("stable", "Stable"),
                        ("declining", "Declining"),
                        ("unknown", "Unknown"),
                    ],
                    default="unknown",
                )),
            ],
            options={
                "db_table": "cymed_rcm_ana_payer_performance",
                "ordering": ["-snapshot_date", "snapshot_period"],
                "unique_together": {("tenant_id", "snapshot_date", "snapshot_period", "insurance_company_id")},
            },
        ),
        migrations.CreateModel(
            name="RCMAIInsight",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("insight_type", models.CharField(
                    max_length=30,
                    choices=[
                        ("denial_prediction", "Denial Prediction"),
                        ("revenue_leakage", "Revenue Leakage"),
                        ("collection_risk", "Collection Risk"),
                        ("auth_delay", "Authorization Delay"),
                        ("coding_error", "Coding Error"),
                        ("payer_performance", "Payer Performance"),
                        ("undercoding", "Undercoding"),
                    ],
                )),
                ("scope_type", models.CharField(
                    max_length=20,
                    choices=[
                        ("claim", "Claim"),
                        ("encounter", "Encounter"),
                        ("patient", "Patient"),
                        ("payer", "Payer"),
                        ("facility", "Facility"),
                    ],
                )),
                ("scope_id", models.UUIDField(db_index=True)),
                ("insight_title", models.CharField(max_length=500)),
                ("insight_detail", models.TextField()),
                ("confidence_score", models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)),
                ("estimated_impact_amount", models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)),
                ("is_advisory_only", models.BooleanField(default=True, editable=False)),
                ("status", models.CharField(
                    max_length=20,
                    choices=[
                        ("pending_review", "Pending Review"),
                        ("acknowledged", "Acknowledged"),
                        ("acted_upon", "Acted Upon"),
                        ("dismissed", "Dismissed"),
                    ],
                    default="pending_review",
                )),
                ("acknowledged_by_user_id", models.UUIDField(null=True, blank=True)),
                ("acknowledged_at", models.DateTimeField(null=True, blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_ana_ai_insights",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="RevenueLeakageAlert",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("alert_date", models.DateField()),
                ("leakage_type", models.CharField(
                    max_length=30,
                    choices=[
                        ("unbilled_charges", "Unbilled Charges"),
                        ("undercoding", "Undercoding"),
                        ("missed_charges", "Missed Charges"),
                        ("expired_auth", "Expired Authorization"),
                        ("timely_filing_risk", "Timely Filing Risk"),
                        ("contract_underpayment", "Contract Underpayment"),
                        ("duplicate_denial", "Duplicate Denial"),
                    ],
                )),
                ("encounter_id", models.UUIDField(null=True, blank=True)),
                ("patient_id", models.UUIDField(null=True, blank=True)),
                ("estimated_leakage_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("status", models.CharField(
                    max_length=20,
                    choices=[
                        ("open", "Open"),
                        ("reviewed", "Reviewed"),
                        ("resolved", "Resolved"),
                        ("false_positive", "False Positive"),
                    ],
                    default="open",
                )),
                ("assigned_to_user_id", models.UUIDField(null=True, blank=True)),
                ("resolution_notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_ana_leakage_alerts",
                "ordering": ["-alert_date", "-created_at"],
            },
        ),
    ]
