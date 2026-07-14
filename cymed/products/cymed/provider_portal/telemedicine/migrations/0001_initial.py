import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProviderTelemedicineSession",
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
                ("patient_id", models.UUIDField(db_index=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("provider_type", models.CharField(max_length=100)),
                (
                    "session_type",
                    models.CharField(
                        choices=[("video", "Video"), ("audio", "Audio"), ("chat", "Chat")],
                        default="video",
                        max_length=20,
                    ),
                ),
                (
                    "visit_type",
                    models.CharField(
                        choices=[
                            ("follow_up", "Follow Up"),
                            ("consultation", "Consultation"),
                            ("second_opinion", "Second Opinion"),
                            ("remote_monitoring", "Remote Monitoring"),
                            ("virtual_round", "Virtual Round"),
                            ("triage", "Triage"),
                        ],
                        default="follow_up",
                        max_length=30,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("scheduled", "Scheduled"),
                            ("waiting", "Waiting"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("no_show", "No Show"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="scheduled",
                        max_length=20,
                    ),
                ),
                ("scheduled_at", models.DateTimeField()),
                ("patient_joined_at", models.DateTimeField(blank=True, null=True)),
                ("provider_joined_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("duration_minutes", models.PositiveIntegerField(blank=True, null=True)),
                ("meeting_url", models.URLField(blank=True)),
                ("meeting_id", models.CharField(blank=True, max_length=255)),
                ("meeting_password", models.CharField(blank=True, max_length=255)),
                ("cymed_patient_session_id", models.UUIDField(blank=True, null=True)),
                ("follow_up_required", models.BooleanField(default=False)),
                ("follow_up_date", models.DateField(blank=True, null=True)),
                ("session_summary", models.TextField(blank=True)),
                ("ai_session_summary", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_prov_tele_sessions",
            },
        ),
        migrations.CreateModel(
            name="ConsultRequest",
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
                ("patient_id", models.UUIDField(db_index=True)),
                ("requesting_provider_id", models.UUIDField(db_index=True)),
                ("requesting_provider_name", models.CharField(max_length=255)),
                ("consulting_provider_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("consulting_specialty", models.CharField(max_length=100)),
                (
                    "urgency",
                    models.CharField(
                        choices=[("routine", "Routine"), ("urgent", "Urgent"), ("stat", "STAT")],
                        default="routine",
                        max_length=20,
                    ),
                ),
                ("consult_reason", models.TextField()),
                ("relevant_history", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("declined", "Declined"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("consult_note_id", models.UUIDField(blank=True, null=True)),
                ("response_summary", models.TextField(blank=True)),
                ("is_telemedicine", models.BooleanField(default=False)),
                ("tele_session_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_prov_consult_requests",
            },
        ),
        migrations.CreateModel(
            name="SecondOpinionRequest",
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
                ("patient_id", models.UUIDField(db_index=True)),
                ("requesting_provider_id", models.UUIDField()),
                ("requested_specialist_id", models.UUIDField(blank=True, null=True)),
                ("requested_specialty", models.CharField(max_length=100)),
                ("clinical_question", models.TextField()),
                ("attached_records", models.JSONField(default=list)),
                (
                    "urgency",
                    models.CharField(
                        choices=[("routine", "Routine"), ("urgent", "Urgent")],
                        default="routine",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("completed", "Completed"),
                            ("declined", "Declined"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("opinion_text", models.TextField(blank=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_prov_second_opinions",
            },
        ),
        migrations.CreateModel(
            name="TelemedicineDocument",
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
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to="cymed_provider_telemedicine.providertelemedicinesession",
                    ),
                ),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("lab_result", "Lab Result"),
                            ("imaging", "Imaging"),
                            ("prescription", "Prescription"),
                            ("referral", "Referral"),
                            ("consent", "Consent"),
                            ("previous_record", "Previous Record"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("file_name", models.CharField(max_length=500)),
                ("file_url", models.URLField()),
                ("file_type", models.CharField(max_length=50)),
                ("file_size_bytes", models.PositiveIntegerField()),
                (
                    "uploaded_by",
                    models.CharField(
                        choices=[("patient", "Patient"), ("provider", "Provider")],
                        max_length=20,
                    ),
                ),
                ("description", models.CharField(blank=True, max_length=500)),
            ],
            options={
                "db_table": "cymed_prov_tele_documents",
            },
        ),
    ]
