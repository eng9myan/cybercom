import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EpidemiologyStudy",
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
                ("study_name", models.CharField(max_length=200)),
                ("study_code", models.CharField(blank=True, max_length=50, null=True, unique=True)),
                (
                    "study_type",
                    models.CharField(
                        choices=[
                            ("cohort", "Cohort"),
                            ("case_control", "Case-Control"),
                            ("cross_sectional", "Cross-Sectional"),
                            ("rct", "Randomised Controlled Trial"),
                            ("surveillance", "Surveillance"),
                            ("registry", "Registry"),
                            ("ecological", "Ecological"),
                        ],
                        max_length=30,
                    ),
                ),
                ("disease_code", models.CharField(blank=True, max_length=20)),
                ("disease_name", models.CharField(blank=True, max_length=200)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("population_scope", models.CharField(blank=True, max_length=200)),
                ("sample_size", models.PositiveIntegerField(blank=True, null=True)),
                ("study_lead_id", models.UUIDField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planning", "Planning"),
                            ("recruiting", "Recruiting"),
                            ("active", "Active"),
                            ("analysis", "Analysis"),
                            ("completed", "Completed"),
                            ("published", "Published"),
                        ],
                        default="planning",
                        max_length=20,
                    ),
                ),
                ("objectives", models.TextField(blank=True)),
                ("methodology", models.TextField(blank=True)),
                ("fhir_research_study_id", models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={"db_table": "cymed_ph_epi_studies"},
        ),
        migrations.CreateModel(
            name="DiseaseTrend",
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
                ("disease_code", models.CharField(max_length=20)),
                ("disease_name", models.CharField(max_length=200)),
                (
                    "period_type",
                    models.CharField(
                        choices=[
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                            ("quarterly", "Quarterly"),
                            ("annual", "Annual"),
                        ],
                        max_length=10,
                    ),
                ),
                ("period_date", models.DateField()),
                ("case_count", models.PositiveIntegerField(default=0)),
                (
                    "incidence_rate",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
                ),
                (
                    "prevalence_rate",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
                ),
                (
                    "mortality_rate",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
                ),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("population_denominator", models.PositiveIntegerField(blank=True, null=True)),
                ("data_source", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "db_table": "cymed_ph_epi_disease_trends",
                "unique_together": {
                    ("tenant_id", "disease_code", "period_type", "period_date", "geographic_scope")
                },
            },
        ),
        migrations.CreateModel(
            name="PopulationIndicator",
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
                ("indicator_code", models.CharField(max_length=50, unique=True)),
                ("indicator_name", models.CharField(max_length=200)),
                (
                    "indicator_type",
                    models.CharField(
                        choices=[
                            ("health_outcome", "Health Outcome"),
                            ("social_determinant", "Social Determinant"),
                            ("health_system", "Health System"),
                            ("demographic", "Demographic"),
                            ("environmental", "Environmental"),
                            ("economic", "Economic"),
                        ],
                        max_length=30,
                    ),
                ),
                ("value", models.DecimalField(decimal_places=4, max_digits=14)),
                ("unit", models.CharField(blank=True, max_length=50)),
                ("measurement_date", models.DateField()),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("data_source", models.CharField(blank=True, max_length=200)),
                ("age_group", models.CharField(blank=True, max_length=50)),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("male", "Male"),
                            ("female", "Female"),
                            ("all", "All"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "confidence_interval_low",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
                ),
                (
                    "confidence_interval_high",
                    models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
                ),
            ],
            options={"db_table": "cymed_ph_epi_indicators"},
        ),
        migrations.CreateModel(
            name="HealthMeasure",
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
                ("measure_name", models.CharField(max_length=200)),
                (
                    "measure_type",
                    models.CharField(
                        choices=[
                            ("morbidity", "Morbidity"),
                            ("mortality", "Mortality"),
                            ("fertility", "Fertility"),
                            ("disability", "Disability"),
                            ("life_expectancy", "Life Expectancy"),
                            ("daly", "DALY"),
                            ("qaly", "QALY"),
                            ("healthy_life_years", "Healthy Life Years"),
                        ],
                        max_length=30,
                    ),
                ),
                ("value", models.DecimalField(decimal_places=4, max_digits=14)),
                ("unit", models.CharField(blank=True, max_length=50)),
                ("period_year", models.PositiveSmallIntegerField()),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("age_group", models.CharField(blank=True, max_length=50)),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("male", "Male"),
                            ("female", "Female"),
                            ("all", "All"),
                        ],
                        max_length=10,
                    ),
                ),
                ("data_source", models.CharField(blank=True, max_length=200)),
                ("icd11_code", models.CharField(blank=True, max_length=20)),
            ],
            options={"db_table": "cymed_ph_epi_health_measures"},
        ),
    ]
