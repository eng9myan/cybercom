import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name="NationalHealthID",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("national_id_number", models.CharField(max_length=100, unique=True)),
                ("id_type", models.CharField(
                    choices=[
                        ("national_id", "National ID"),
                        ("resident_id", "Resident ID"),
                        ("passport", "Passport"),
                        ("gulfid", "Gulf ID"),
                        ("other", "Other"),
                    ],
                    default="national_id",
                    max_length=20,
                )),
                ("id_status", models.CharField(
                    choices=[
                        ("active", "Active"),
                        ("suspended", "Suspended"),
                        ("revoked", "Revoked"),
                        ("pending_verification", "Pending Verification"),
                    ],
                    default="pending_verification",
                    max_length=20,
                )),
                ("issued_date", models.DateField()),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("issuing_authority", models.CharField(blank=True, max_length=200)),
                ("verification_date", models.DateField(blank=True, null=True)),
                ("verified_by_user_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_ph_dh_national_ids",
                "unique_together": {("tenant_id", "patient_id")},
            },
        ),
        migrations.CreateModel(
            name="VaccinationCertificate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("vaccine_name", models.CharField(max_length=200)),
                ("vaccine_code", models.CharField(blank=True, max_length=50)),
                ("dose_number", models.PositiveSmallIntegerField(default=1)),
                ("total_doses", models.PositiveSmallIntegerField(default=1)),
                ("vaccination_date", models.DateField()),
                ("facility_id", models.UUIDField(blank=True, null=True)),
                ("provider_id", models.UUIDField(blank=True, null=True)),
                ("batch_number", models.CharField(blank=True, max_length=100)),
                ("certificate_number", models.CharField(max_length=100, unique=True)),
                ("validity_start", models.DateField()),
                ("validity_end", models.DateField(blank=True, null=True)),
                ("qr_code_data", models.TextField(blank=True)),
                ("certificate_status", models.CharField(
                    choices=[
                        ("valid", "Valid"),
                        ("expired", "Expired"),
                        ("revoked", "Revoked"),
                        ("pending", "Pending"),
                    ],
                    default="valid",
                    max_length=20,
                )),
                ("is_international", models.BooleanField(default=False)),
                ("fhir_immunization_id", models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={"db_table": "cymed_ph_dh_vaccination_certs"},
        ),
        migrations.CreateModel(
            name="HealthPass",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("pass_type", models.CharField(
                    choices=[
                        ("travel", "Travel"),
                        ("event", "Event"),
                        ("workplace", "Workplace"),
                        ("education", "Education"),
                        ("healthcare_access", "Healthcare Access"),
                    ],
                    max_length=20,
                )),
                ("pass_name", models.CharField(max_length=200)),
                ("valid_from", models.DateField()),
                ("valid_until", models.DateField(blank=True, null=True)),
                ("conditions_met", models.JSONField(default=list)),
                ("pass_status", models.CharField(
                    choices=[
                        ("active", "Active"),
                        ("expired", "Expired"),
                        ("revoked", "Revoked"),
                        ("suspended", "Suspended"),
                    ],
                    default="active",
                    max_length=20,
                )),
                ("qr_code_data", models.TextField(blank=True)),
                ("issued_by_authority", models.CharField(blank=True, max_length=200)),
                ("revocation_reason", models.CharField(blank=True, max_length=500)),
            ],
            options={"db_table": "cymed_ph_dh_health_passes"},
        ),
        migrations.CreateModel(
            name="DigitalHealthWalletEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("entry_type", models.CharField(
                    choices=[
                        ("medical_record", "Medical Record"),
                        ("vaccination_certificate", "Vaccination Certificate"),
                        ("insurance_card", "Insurance Card"),
                        ("prescription", "Prescription"),
                        ("lab_result", "Lab Result"),
                        ("imaging_report", "Imaging Report"),
                        ("allergy_record", "Allergy Record"),
                        ("health_pass", "Health Pass"),
                        ("other", "Other"),
                    ],
                    max_length=30,
                )),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("content_reference", models.CharField(blank=True, max_length=500)),
                ("issue_date", models.DateField()),
                ("validity_date", models.DateField(blank=True, null=True)),
                ("issuing_authority", models.CharField(blank=True, max_length=200)),
                ("issuing_facility_id", models.UUIDField(blank=True, null=True)),
                ("is_shareable", models.BooleanField(default=True)),
                ("is_verified", models.BooleanField(default=False)),
                ("verification_source", models.CharField(blank=True, max_length=200)),
                ("qr_code_data", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_ph_dh_wallet_entries"},
        ),
    ]
