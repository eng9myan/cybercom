import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PortalPrescriptionView",
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
                ("cymed_prescription_id", models.UUIDField(db_index=True)),
                ("prescription_number", models.CharField(db_index=True, max_length=100)),
                ("pharmacy_name", models.CharField(blank=True, max_length=255)),
                ("pharmacy_id", models.UUIDField(blank=True, null=True)),
                ("prescriber_name", models.CharField(blank=True, max_length=255)),
                ("prescription_type", models.CharField(blank=True, max_length=30)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("dispensed", "Dispensed"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                            ("expired", "Expired"),
                            ("on_hold", "On Hold"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("is_controlled", models.BooleanField(default=False)),
                ("items_summary", models.JSONField(default=list)),
                ("prescribed_at", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateField(blank=True, null=True)),
                ("refills_authorized", models.PositiveSmallIntegerField(default=0)),
                ("refills_dispensed", models.PositiveSmallIntegerField(default=0)),
                ("can_request_refill", models.BooleanField(default=False)),
                ("is_viewed", models.BooleanField(default=False)),
                ("viewed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "fhir_medication_request_id",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
            ],
            options={
                "db_table": "cymed_portal_prescriptions",
            },
        ),
        migrations.CreateModel(
            name="RefillRequest",
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
                (
                    "portal_prescription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refill_requests",
                        to="cymed_portal_prescriptions.portalprescriptionview",
                    ),
                ),
                ("preferred_pharmacy_id", models.UUIDField(blank=True, null=True)),
                ("preferred_pharmacy_name", models.CharField(blank=True, max_length=255)),
                (
                    "pickup_method",
                    models.CharField(
                        choices=[
                            ("counter", "Counter Pickup"),
                            ("delivery", "Delivery"),
                            ("mail", "Mail"),
                        ],
                        default="counter",
                        max_length=20,
                    ),
                ),
                ("delivery_address", models.CharField(blank=True, max_length=500)),
                ("notes", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("received_by_pharmacy", "Received by Pharmacy"),
                            ("processing", "Processing"),
                            ("ready", "Ready"),
                            ("dispensed", "Dispensed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="submitted",
                        max_length=30,
                    ),
                ),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("pharmacy_response", models.TextField(blank=True)),
                ("estimated_ready_at", models.DateTimeField(blank=True, null=True)),
                ("cymed_dispense_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_refill_requests",
            },
        ),
        migrations.CreateModel(
            name="MedicationInstruction",
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
                ("drug_code", models.CharField(db_index=True, max_length=100)),
                ("drug_name", models.CharField(max_length=500)),
                ("instruction_text", models.TextField()),
                ("instruction_text_ar", models.TextField(blank=True)),
                ("dose", models.CharField(blank=True, max_length=100)),
                ("frequency", models.CharField(blank=True, max_length=100)),
                ("route", models.CharField(blank=True, max_length=100)),
                ("special_warnings", models.JSONField(default=list)),
                ("side_effects", models.JSONField(default=list)),
                ("ai_explanation", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_portal_medication_instructions",
            },
        ),
        migrations.CreateModel(
            name="MedicationAdherenceLog",
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
                (
                    "portal_prescription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adherence_logs",
                        to="cymed_portal_prescriptions.portalprescriptionview",
                    ),
                ),
                ("drug_code", models.CharField(max_length=100)),
                ("drug_name", models.CharField(max_length=500)),
                ("scheduled_time", models.DateTimeField()),
                ("taken_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("taken", "Taken"),
                            ("missed", "Missed"),
                            ("skipped", "Skipped"),
                            ("rescheduled", "Rescheduled"),
                        ],
                        default="taken",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_portal_adherence_logs",
            },
        ),
        migrations.AddIndex(
            model_name="portalprescriptionview",
            index=models.Index(
                fields=["account_id", "status"],
                name="prescriptions_acct_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="portalprescriptionview",
            index=models.Index(
                fields=["patient_id", "prescribed_at"],
                name="prescriptions_patient_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="refillrequest",
            index=models.Index(
                fields=["account_id", "status"],
                name="refill_requests_acct_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="medicationadherencelog",
            index=models.Index(
                fields=["account_id", "status", "scheduled_time"],
                name="adherence_logs_acct_status_time_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="medicationinstruction",
            unique_together={("tenant_id", "patient_id", "drug_code")},
        ),
    ]
