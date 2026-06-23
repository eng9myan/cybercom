import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProviderWorkspace",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_type", models.CharField(
                    choices=[
                        ("physician", "Physician"),
                        ("consultant", "Consultant"),
                        ("resident", "Resident"),
                        ("nurse", "Nurse"),
                        ("charge_nurse", "Charge Nurse"),
                        ("pharmacist", "Pharmacist"),
                        ("clinical_pharmacist", "Clinical Pharmacist"),
                        ("radiologist", "Radiologist"),
                        ("lab_technologist", "Lab Technologist"),
                        ("microbiologist", "Microbiologist"),
                        ("pathologist", "Pathologist"),
                        ("therapist", "Therapist"),
                        ("care_coordinator", "Care Coordinator"),
                        ("administrator", "Administrator"),
                    ],
                    max_length=30,
                )),
                ("cyidentity_user_id", models.UUIDField()),
                ("is_active", models.BooleanField(default=True)),
                ("last_active_at", models.DateTimeField(blank=True, null=True)),
                ("preferred_specialty", models.CharField(blank=True, max_length=255)),
                ("home_unit_id", models.UUIDField(blank=True, null=True)),
                ("home_unit_name", models.CharField(blank=True, max_length=255)),
                ("department", models.CharField(blank=True, max_length=255)),
                ("language", models.CharField(default="en", max_length=10)),
                ("timezone", models.CharField(default="UTC", max_length=100)),
            ],
            options={"db_table": "cymed_prov_workspaces", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ProviderDashboard",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("workspace", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="dashboard",
                    to="cymed_provider_workspace.providerworkspace",
                )),
                ("layout_config", models.JSONField(default=dict)),
                ("pinned_patient_ids", models.JSONField(default=list)),
                ("active_patient_list_id", models.UUIDField(blank=True, null=True)),
                ("show_tasks", models.BooleanField(default=True)),
                ("show_results", models.BooleanField(default=True)),
                ("show_messages", models.BooleanField(default=True)),
                ("show_schedule", models.BooleanField(default=True)),
                ("show_approvals", models.BooleanField(default=True)),
                ("show_census", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_prov_dashboards"},
        ),
        migrations.CreateModel(
            name="ProviderPreferences",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("workspace", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="preferences",
                    to="cymed_provider_workspace.providerworkspace",
                )),
                ("default_note_template", models.CharField(blank=True, max_length=255)),
                ("smart_phrase_favorites", models.JSONField(default=list)),
                ("result_critical_alert_sound", models.BooleanField(default=True)),
                ("task_notification_push", models.BooleanField(default=True)),
                ("task_notification_email", models.BooleanField(default=True)),
                ("message_notification_push", models.BooleanField(default=True)),
                ("handoff_auto_include_summary", models.BooleanField(default=True)),
                ("ai_suggestions_enabled", models.BooleanField(default=True)),
                ("voice_dictation_enabled", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_prov_preferences"},
        ),
        migrations.CreateModel(
            name="WorkspaceSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("workspace", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sessions",
                    to="cymed_provider_workspace.providerworkspace",
                )),
                ("session_token", models.CharField(max_length=512, unique=True)),
                ("device_type", models.CharField(
                    choices=[
                        ("desktop", "Desktop"),
                        ("tablet", "Tablet"),
                        ("mobile", "Mobile"),
                    ],
                    max_length=20,
                )),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("context_patient_id", models.UUIDField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_sessions", "ordering": ["-started_at"]},
        ),
        migrations.AddIndex(
            model_name="providerworkspace",
            index=models.Index(fields=["tenant_id", "provider_id"], name="cymed_prov_wkspc_tenant_prov_idx"),
        ),
        migrations.AddIndex(
            model_name="providerworkspace",
            index=models.Index(fields=["tenant_id", "is_active"], name="cymed_prov_wkspc_tenant_active_idx"),
        ),
        migrations.AddIndex(
            model_name="workspacesession",
            index=models.Index(fields=["tenant_id", "workspace", "is_active"], name="cymed_prov_sess_tenant_wkspc_idx"),
        ),
        migrations.AddIndex(
            model_name="workspacesession",
            index=models.Index(fields=["tenant_id", "started_at"], name="cymed_prov_sess_tenant_started_idx"),
        ),
    ]
