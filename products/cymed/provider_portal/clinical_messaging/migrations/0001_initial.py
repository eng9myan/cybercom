import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ClinicalMessageThread",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("thread_type", models.CharField(
                    choices=[
                        ("direct", "Direct"),
                        ("team", "Team"),
                        ("patient_discussion", "Patient Discussion"),
                        ("handoff", "Handoff"),
                        ("consult_request", "Consult Request"),
                        ("escalation", "Escalation"),
                        ("clinical_group", "Clinical Group"),
                    ],
                    max_length=30,
                )),
                ("subject", models.CharField(blank=True, max_length=500)),
                ("patient_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                ("status", models.CharField(
                    choices=[
                        ("active", "Active"),
                        ("archived", "Archived"),
                        ("resolved", "Resolved"),
                    ],
                    default="active",
                    max_length=20,
                )),
                ("is_urgent", models.BooleanField(default=False)),
                ("is_encrypted", models.BooleanField(default=True)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("unread_count", models.PositiveIntegerField(default=0)),
                ("cyconnect_thread_id", models.UUIDField(blank=True, null=True)),
                ("created_by_provider_id", models.UUIDField()),
            ],
            options={"db_table": "cymed_prov_msg_threads", "ordering": ["-last_message_at"]},
        ),
        migrations.CreateModel(
            name="ClinicalMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("thread", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="messages",
                    to="cymed_provider_clinical_messaging.clinicalmessagethread",
                )),
                ("sender_provider_id", models.UUIDField(db_index=True)),
                ("sender_name", models.CharField(max_length=255)),
                ("sender_type", models.CharField(max_length=50)),
                ("body", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("is_system_message", models.BooleanField(default=False)),
                ("priority", models.CharField(
                    choices=[
                        ("routine", "Routine"),
                        ("urgent", "Urgent"),
                        ("stat", "STAT"),
                    ],
                    default="routine",
                    max_length=20,
                )),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "cymed_prov_messages", "ordering": ["-sent_at"]},
        ),
        migrations.CreateModel(
            name="MessageAttachment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("message", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="attachments",
                    to="cymed_provider_clinical_messaging.clinicalmessage",
                )),
                ("file_name", models.CharField(max_length=500)),
                ("file_url", models.URLField(max_length=2000)),
                ("file_type", models.CharField(max_length=100)),
                ("file_size_bytes", models.PositiveIntegerField()),
                ("attachment_type", models.CharField(
                    choices=[
                        ("lab_result", "Lab Result"),
                        ("imaging", "Imaging"),
                        ("document", "Document"),
                        ("photo", "Photo"),
                        ("other", "Other"),
                    ],
                    default="other",
                    max_length=30,
                )),
                ("description", models.CharField(blank=True, max_length=500)),
            ],
            options={"db_table": "cymed_prov_msg_attachments", "ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="ClinicalGroup",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("name", models.CharField(max_length=255)),
                ("group_type", models.CharField(
                    choices=[
                        ("department", "Department"),
                        ("unit", "Unit"),
                        ("specialty", "Specialty"),
                        ("on_call", "On Call"),
                        ("committee", "Committee"),
                        ("ad_hoc", "Ad Hoc"),
                    ],
                    max_length=30,
                )),
                ("description", models.TextField(blank=True)),
                ("members", models.JSONField(default=list)),
                ("admin_provider_id", models.UUIDField()),
                ("is_active", models.BooleanField(default=True)),
                ("message_retention_days", models.PositiveIntegerField(default=365)),
            ],
            options={"db_table": "cymed_prov_clinical_groups", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="MessageThreadParticipant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("thread", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="participants",
                    to="cymed_provider_clinical_messaging.clinicalmessagethread",
                )),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("provider_type", models.CharField(max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("last_read_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_msg_participants", "ordering": ["joined_at"]},
        ),
        migrations.AddIndex(
            model_name="clinicalmessagethread",
            index=models.Index(fields=["tenant_id", "status", "last_message_at"], name="cymed_prov_thread_status_msg_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalmessagethread",
            index=models.Index(fields=["tenant_id", "patient_id"], name="cymed_prov_thread_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalmessagethread",
            index=models.Index(fields=["tenant_id", "is_urgent", "status"], name="cymed_prov_thread_urgent_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalmessage",
            index=models.Index(fields=["tenant_id", "thread", "sent_at"], name="cymed_prov_msg_thread_sent_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalmessage",
            index=models.Index(fields=["tenant_id", "sender_provider_id", "sent_at"], name="cymed_prov_msg_sender_sent_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalmessage",
            index=models.Index(fields=["tenant_id", "is_read", "priority"], name="cymed_prov_msg_read_priority_idx"),
        ),
        migrations.AddIndex(
            model_name="messageattachment",
            index=models.Index(fields=["tenant_id", "message"], name="cymed_prov_msgattach_msg_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalgroup",
            index=models.Index(fields=["tenant_id", "group_type", "is_active"], name="cymed_prov_group_type_active_idx"),
        ),
        migrations.AddIndex(
            model_name="messagethreadparticipant",
            index=models.Index(fields=["tenant_id", "thread", "provider_id"], name="cymed_prov_participant_thread_idx"),
        ),
        migrations.AddIndex(
            model_name="messagethreadparticipant",
            index=models.Index(fields=["tenant_id", "provider_id", "is_active"], name="cymed_prov_participant_prov_idx"),
        ),
    ]
