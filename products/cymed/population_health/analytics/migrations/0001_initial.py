import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NationalHealthSnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("snapshot_date", models.DateField()),
                ("period_type", models.CharField(
                    choices=[
                        ("daily", "Daily"),
                        ("weekly", "Weekly"),
                        ("monthly", "Monthly"),
                        ("quarterly", "Quarterly"),
                        ("annual", "Annual"),
                    ],
                    max_length=10,
                )),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("total_population", models.PositiveIntegerField(default=0)),
                ("registered_patients", models.PositiveIntegerField(default=0)),
                ("disease_prevalence", models.JSONField(default=dict)),
                ("vaccination_coverage", models.JSONField(default=dict)),
                ("care_gap_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("risk_distribution", models.JSONField(default=dict)),
                ("active_outbreaks", models.PositiveIntegerField(default=0)),
                ("program_enrollment_count", models.PositiveIntegerField(default=0)),
                ("quality_score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
            ],
            options={
                "db_table": "cymed_ph_ana_health_snapshots",
                "unique_together": {("tenant_id", "snapshot_date", "period_type", "geographic_scope")},
            },
        ),
        migrations.CreateModel(
            name="PopulationAnalyticsInsight",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("insight_type", models.CharField(
                    choices=[
                        ("disease_trend", "Disease Trend"),
                        ("care_gap", "Care Gap"),
                        ("risk_pattern", "Risk Pattern"),
                        ("program_effectiveness", "Program Effectiveness"),
                        ("outbreak_risk", "Outbreak Risk"),
                        ("vaccination_gap", "Vaccination Gap"),
                        ("quality_gap", "Quality Gap"),
                        ("population_shift", "Population Shift"),
                    ],
                    max_length=30,
                )),
                ("scope_type", models.CharField(
                    choices=[
                        ("patient", "Patient"),
                        ("population_group", "Population Group"),
                        ("facility", "Facility"),
                        ("region", "Region"),
                        ("national", "National"),
                    ],
                    max_length=20,
                )),
                ("scope_id", models.UUIDField(blank=True, null=True)),
                ("insight_title", models.CharField(max_length=500)),
                ("insight_detail", models.TextField()),
                ("confidence_score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("estimated_impact", models.TextField(blank=True)),
                ("is_ai_generated", models.BooleanField(default=False)),
                ("is_advisory_only", models.BooleanField(default=True, editable=False)),
                ("status", models.CharField(
                    choices=[
                        ("pending_review", "Pending Review"),
                        ("acknowledged", "Acknowledged"),
                        ("acted_upon", "Acted Upon"),
                        ("dismissed", "Dismissed"),
                    ],
                    default="pending_review",
                    max_length=20,
                )),
                ("acknowledged_by_user_id", models.UUIDField(blank=True, null=True)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_ph_ana_insights"},
        ),
        migrations.CreateModel(
            name="QualityKPIDashboard",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("kpi_name", models.CharField(max_length=200)),
                ("kpi_category", models.CharField(
                    choices=[
                        ("clinical_quality", "Clinical Quality"),
                        ("patient_safety", "Patient Safety"),
                        ("access", "Access"),
                        ("efficiency", "Efficiency"),
                        ("patient_experience", "Patient Experience"),
                        ("population_health", "Population Health"),
                    ],
                    max_length=30,
                )),
                ("facility_id", models.UUIDField(blank=True, null=True)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("current_value", models.DecimalField(decimal_places=2, max_digits=10)),
                ("target_value", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("unit", models.CharField(blank=True, max_length=50)),
                ("meets_target", models.BooleanField(default=False)),
                ("trend_direction", models.CharField(
                    choices=[
                        ("improving", "Improving"),
                        ("stable", "Stable"),
                        ("declining", "Declining"),
                        ("unknown", "Unknown"),
                    ],
                    default="unknown",
                    max_length=10,
                )),
            ],
            options={"db_table": "cymed_ph_ana_quality_kpis"},
        ),
        migrations.CreateModel(
            name="OutbreakForecast",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("disease_code", models.CharField(max_length=20)),
                ("disease_name", models.CharField(max_length=200)),
                ("forecast_date", models.DateField()),
                ("forecast_period_days", models.PositiveSmallIntegerField(default=30)),
                ("predicted_cases", models.PositiveIntegerField(blank=True, null=True)),
                ("confidence_interval_low", models.PositiveIntegerField(blank=True, null=True)),
                ("confidence_interval_high", models.PositiveIntegerField(blank=True, null=True)),
                ("risk_level", models.CharField(
                    choices=[
                        ("low", "Low"),
                        ("medium", "Medium"),
                        ("high", "High"),
                        ("critical", "Critical"),
                    ],
                    default="low",
                    max_length=10,
                )),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("is_ai_generated", models.BooleanField(default=False)),
                ("is_advisory_only", models.BooleanField(default=True, editable=False)),
                ("model_version", models.CharField(blank=True, max_length=50)),
            ],
            options={"db_table": "cymed_ph_ana_outbreak_forecasts"},
        ),
        migrations.CreateModel(
            name="PopulationHealthDashboard",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("dashboard_name", models.CharField(max_length=200)),
                ("dashboard_type", models.CharField(
                    choices=[
                        ("population_health", "Population Health"),
                        ("registry", "Registry"),
                        ("public_health", "Public Health"),
                        ("national", "National"),
                        ("ministry", "Ministry"),
                        ("surveillance", "Surveillance"),
                    ],
                    max_length=30,
                )),
                ("facility_id", models.UUIDField(blank=True, null=True)),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("as_of_date", models.DateField()),
                ("total_enrolled_patients", models.PositiveIntegerField(default=0)),
                ("high_risk_patients", models.PositiveIntegerField(default=0)),
                ("open_care_gaps", models.PositiveIntegerField(default=0)),
                ("active_programs", models.PositiveIntegerField(default=0)),
                ("vaccination_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("disease_registry_count", models.PositiveIntegerField(default=0)),
                ("kpi_summary", models.JSONField(default=dict)),
            ],
            options={"db_table": "cymed_ph_ana_dashboards"},
        ),
    ]
