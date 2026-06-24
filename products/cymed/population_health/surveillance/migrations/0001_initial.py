mport django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name="SurveillanceCase",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("disease_code", models.CharField(max_length=20)),
                ("disease_name", models.CharField(max_length=200)),
                ("case_type", models.CharField(
                    choices=[
                        ("confirmed", "Confirmed"),
                        ("probable", "Probable"),
                        ("suspected", "Suspected"),
                        ("not_a_case", "Not a Case"),
                    ],
                    default="suspected",
                    max_length=20,
                )),
                ("case_date", models.DateField()),
                ("reporting_facility_id", models.UUIDField(blank=True, null=True)),
                ("reporting_provider_id", models.UUIDField(blank=True, null=True)),
                ("status", models.CharField(
                    choices=[
                        ("open", "Open"),
                        ("under_investigation", "Under Investigation"),
                        ("closed", "Closed"),
                        ("discarded", "Discarded"),
                    ],
                    default="open",
                    max_length=20,
                )),
                ("is_notifiable", models.BooleanField(default=False)),
                ("outbreak_id", models.UUIDField(blank=True, null=True)),
                ("notification_sent", models.BooleanField(default=False)),
                ("notification_sent_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_ph_surv_cases"},
        ),
        migrations.CreateModel(
            name="Outbreak",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("disease_code", models.CharField(max_length=20)),
                ("disease_name", models.CharField(max_length=200)),
                ("outbreak_type", models.CharField(
                    choices=[
                        ("epidemic", "Epidemic"),
                        ("cluster", "Cluster"),
                        ("sporadic", "Sporadic"),
                        ("endemic", "Endemic"),
                    ],
                    default="cluster",
                    max_length=20,
                )),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("affected_count", models.PositiveIntegerField(default=0)),
                ("suspected_count", models.PositiveIntegerField(default=0)),
                ("confirmed_count", models.PositiveIntegerField(default=0)),
                ("deaths_count", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(
                    choices=[
                        ("active", "Active"),
                        ("contained", "Contained"),
                        ("resolved", "Resolved"),
                        ("monitoring", "Monitoring"),
                    ],
                    default="active",
                    max_length=20,
                )),
                ("severity_level", models.CharField(
                    choices=[
                        ("low", "Low"),
                        ("medium", "Medium"),
                        ("high", "High"),
                        ("critical", "Critical"),
                    ],
                    default="low",
                    max_length=10,
                )),
                ("is_reported_to_authority", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_ph_surv_outbreaks"},
        ),
        migrations.CreateModel(
            name="OutbreakAlert",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("outbreak", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="alerts",
                    to="cymed_ph_surveillance.outbreak",
                )),
                ("alert_level", models.CharField(
                    choices=[
                        ("green", "Green"),
                        ("yellow", "Yellow"),
                        ("orange", "Orange"),
                        ("red", "Red"),
                    ],
                    default="yellow",
                    max_length=10,
                )),
                ("alert_date", models.DateTimeField(auto_now_add=True)),
                ("description", models.TextField()),
                ("issued_by_authority", models.CharField(blank=True, max_length=200)),
                ("recommended_actions", models.JSONField(default=list)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_ph_surv_outbreak_alerts"},
        ),
        migrations.CreateModel(
            name="PublicHealthEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("event_type", models.CharField(
                    choices=[
                        ("disease_surge", "Disease Surge"),
                        ("mass_gathering", "Mass Gathering"),
                        ("natural_disaster", "Natural Disaster"),
                        ("environmental_hazard", "Environmental Hazard"),
                        ("food_contamination", "Food Contamination"),
                        ("chemical_exposure", "Chemical Exposure"),
                        ("vaccination_drive", "Vaccination Drive"),
                        ("health_campaign", "Health Campaign"),
                        ("other", "Other"),
                    ],
                    max_length=30,
                )),
                ("event_name", models.CharField(max_length=200)),
                ("event_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("description", models.TextField(blank=True)),
                ("geographic_scope", models.CharField(blank=True, max_length=200)),
                ("severity", models.CharField(
                    choices=[
                        ("low", "Low"),
                        ("medium", "Medium"),
                        ("high", "High"),
                        ("critical", "Critical"),
                    ],
                    default="low",
                    max_length=10,
                )),
                ("response_status", models.CharField(
                    choices=[
                        ("planning", "Planning"),
                        ("active", "Active"),
                        ("completed", "Completed"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="planning",
                    max_length=20,
                )),
                ("responsible_authority", models.CharField(blank=True, max_length=200)),
            ],
            options={"db_table": "cymed_ph_surv_public_health_events"},
        ),
        migrations.CreateModel(
            name="CaseInvestigation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("surveillance_case", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="investigations",
                    to="cymed_ph_surveillance.surveillancecase",
                )),
                ("investigator_id", models.UUIDField()),
                ("investigation_date", models.DateField()),
                ("exposure_history", models.TextField(blank=True)),
                ("probable_source", models.CharField(blank=True, max_length=500)),
                ("contacts_identified", models.PositiveIntegerField(default=0)),
                ("contacts_traced", models.PositiveIntegerField(default=0)),
                ("contacts_tested", models.PositiveIntegerField(default=0)),
                ("outcome", models.CharField(
                    choices=[
                        ("resolved", "Resolved"),
                        ("ongoing", "Ongoing"),
                        ("referred", "Referred"),
                        ("closed", "Closed"),
                    ],
                    default="ongoing",
                    max_length=30,
                )),
                ("findings", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_ph_surv_case_investigations"},
        ),
    ]
