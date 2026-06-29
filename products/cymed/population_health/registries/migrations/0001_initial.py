import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DiseaseRegistry",
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
                    "registry_type",
                    models.CharField(
                        choices=[
                            ("cancer", "Cancer"),
                            ("diabetes", "Diabetes"),
                            ("cardiology", "Cardiology"),
                            ("stroke", "Stroke"),
                            ("maternal", "Maternal"),
                            ("child_health", "Child Health"),
                            ("rare_disease", "Rare Disease"),
                            ("mental_health", "Mental Health"),
                            ("vaccination", "Vaccination"),
                            ("chronic_kidney", "Chronic Kidney"),
                            ("hypertension", "Hypertension"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("icd11_codes", models.JSONField(default=list)),
                ("is_national", models.BooleanField(default=False)),
                ("managing_authority", models.CharField(blank=True, max_length=200)),
                ("start_date", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                (
                    "registry_code",
                    models.CharField(blank=True, max_length=50, null=True, unique=True),
                ),
                ("fhir_list_id", models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={"db_table": "cymed_ph_reg_registries"},
        ),
        migrations.CreateModel(
            name="RegistryPatient",
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
                    "registry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="patients",
                        to="cymed_ph_registries.diseaseregistry",
                    ),
                ),
                ("patient_id", models.UUIDField(db_index=True)),
                ("enrollment_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("inactive", "Inactive"),
                            ("deceased", "Deceased"),
                            ("transferred", "Transferred"),
                            ("withdrawn", "Withdrawn"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("national_id_hash", models.CharField(blank=True, max_length=200)),
                (
                    "enrollment_source",
                    models.CharField(
                        choices=[
                            ("clinical", "Clinical"),
                            ("laboratory", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("pharmacy", "Pharmacy"),
                            ("self_referral", "Self Referral"),
                            ("external", "External"),
                        ],
                        default="clinical",
                        max_length=30,
                    ),
                ),
                ("primary_icd11_code", models.CharField(blank=True, max_length=20)),
            ],
            options={
                "db_table": "cymed_ph_reg_patients",
                "unique_together": {("tenant_id", "registry", "patient_id")},
            },
        ),
        migrations.CreateModel(
            name="RegistryEnrollment",
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
                    "registry_patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="cymed_ph_registries.registrypatient",
                    ),
                ),
                ("enrolling_provider_id", models.UUIDField(blank=True, null=True)),
                ("enrolling_facility_id", models.UUIDField(blank=True, null=True)),
                ("enrollment_criteria_met", models.JSONField(default=list)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_ph_reg_enrollments"},
        ),
        migrations.CreateModel(
            name="RegistryStatus",
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
                    "registry_patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="cymed_ph_registries.registrypatient",
                    ),
                ),
                ("status_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("inactive", "Inactive"),
                            ("deceased", "Deceased"),
                            ("transferred", "Transferred"),
                            ("withdrawn", "Withdrawn"),
                        ],
                        max_length=20,
                    ),
                ),
                ("changed_by_user_id", models.UUIDField(blank=True, null=True)),
                ("reason", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_ph_reg_status_history"},
        ),
        migrations.CreateModel(
            name="RegistryOutcome",
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
                    "registry_patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outcomes",
                        to="cymed_ph_registries.registrypatient",
                    ),
                ),
                (
                    "outcome_type",
                    models.CharField(
                        choices=[
                            ("remission", "Remission"),
                            ("progression", "Progression"),
                            ("complication", "Complication"),
                            ("recovery", "Recovery"),
                            ("death", "Death"),
                            ("transfer", "Transfer"),
                            ("lost_to_followup", "Lost to Follow-up"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("outcome_date", models.DateField()),
                ("icd11_code", models.CharField(blank=True, max_length=20)),
                ("outcome_description", models.TextField(blank=True)),
                ("reporting_provider_id", models.UUIDField(blank=True, null=True)),
                (
                    "severity",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("mild", "Mild"),
                            ("moderate", "Moderate"),
                            ("severe", "Severe"),
                            ("critical", "Critical"),
                        ],
                        max_length=20,
                    ),
                ),
            ],
            options={"db_table": "cymed_ph_reg_outcomes"},
        ),
    ]
