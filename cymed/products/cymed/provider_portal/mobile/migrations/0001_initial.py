import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProviderMobileDevice",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                (
                    "provider_workspace_id",
                    models.UUIDField(blank=True, null=True),
                ),
                ("device_name", models.CharField(max_length=255)),
                (
                    "device_type",
                    models.CharField(
                        choices=[
                            ("ios", "iOS"),
                            ("android", "Android"),
                            ("tablet", "Tablet"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "push_token",
                    models.CharField(blank=True, db_index=True, max_length=512),
                ),
                ("device_fingerprint", models.CharField(blank=True, max_length=255)),
                ("platform_version", models.CharField(blank=True, max_length=50)),
                ("app_version", models.CharField(blank=True, max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("is_trusted", models.BooleanField(default=False)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("registered_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "cymed_prov_mobile_devices",
            },
        ),
        migrations.CreateModel(
            name="MobileSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="cymed_provider_mobile.providermobiledevice",
                    ),
                ),
                ("provider_id", models.UUIDField(db_index=True)),
                ("session_token", models.CharField(max_length=512, unique=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "context_patient_id",
                    models.UUIDField(blank=True, null=True),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("biometric_verified", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "cymed_prov_mobile_sessions",
            },
        ),
        migrations.CreateModel(
            name="MobilePreferences",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "device",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preferences",
                        to="cymed_provider_mobile.providermobiledevice",
                    ),
                ),
                ("provider_id", models.UUIDField()),
                (
                    "home_tab",
                    models.CharField(
                        choices=[
                            ("dashboard", "Dashboard"),
                            ("patient_lists", "Patient Lists"),
                            ("tasks", "Tasks"),
                            ("results", "Results"),
                            ("messages", "Messages"),
                        ],
                        default="dashboard",
                        max_length=20,
                    ),
                ),
                ("push_critical_results", models.BooleanField(default=True)),
                ("push_task_alerts", models.BooleanField(default=True)),
                ("push_messages", models.BooleanField(default=True)),
                ("push_approval_requests", models.BooleanField(default=True)),
                ("biometric_login", models.BooleanField(default=True)),
                ("quick_action_1", models.CharField(blank=True, max_length=100)),
                ("quick_action_2", models.CharField(blank=True, max_length=100)),
                ("offline_patient_ids", models.JSONField(default=list)),
            ],
            options={
                "db_table": "cymed_prov_mobile_preferences",
            },
        ),
        migrations.CreateModel(
            name="MobilePushNotification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("device_id", models.UUIDField(blank=True, db_index=True, null=True)),
                (
                    "notification_type",
                    models.CharField(
                        choices=[
                            ("critical_result", "Critical Result"),
                            ("task_assigned", "Task Assigned"),
                            ("task_overdue", "Task Overdue"),
                            ("message_received", "Message Received"),
                            ("approval_required", "Approval Required"),
                            ("round_starting", "Round Starting"),
                            ("credential_expiry", "Credential Expiry"),
                            ("schedule_change", "Schedule Change"),
                            ("patient_deterioration", "Patient Deterioration"),
                            ("system_alert", "System Alert"),
                        ],
                        max_length=30,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("action_type", models.CharField(blank=True, max_length=100)),
                ("action_id", models.UUIDField(blank=True, null=True)),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("normal", "Normal"),
                            ("high", "High"),
                            ("critical", "Critical"),
                        ],
                        default="normal",
                        max_length=10,
                    ),
                ),
                ("is_delivered", models.BooleanField(default=False)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("source_type", models.CharField(blank=True, max_length=100)),
                ("source_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_prov_mobile_notifications",
            },
        ),
        # Indexes
        migrations.AddIndex(
            model_name="mobilepushnotification",
            index=models.Index(
                fields=["tenant_id", "provider_id", "is_read", "created_at"],
                name="cymed_prov_notif_idx",
            ),
        ),
    ]
