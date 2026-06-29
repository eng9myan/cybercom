import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PatientNotification",
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
                    "notification_type",
                    models.CharField(
                        choices=[
                            ("appointment_confirmed", "Appointment Confirmed"),
                            ("appointment_reminder", "Appointment Reminder"),
                            ("appointment_cancelled", "Appointment Cancelled"),
                            ("lab_result_ready", "Lab Result Ready"),
                            ("imaging_result_ready", "Imaging Result Ready"),
                            ("prescription_ready", "Prescription Ready"),
                            ("refill_reminder", "Refill Reminder"),
                            ("invoice_due", "Invoice Due"),
                            ("payment_received", "Payment Received"),
                            ("preauth_approved", "Preauth Approved"),
                            ("preauth_denied", "Preauth Denied"),
                            ("message_received", "Message Received"),
                            ("critical_result", "Critical Result"),
                            ("system_alert", "System Alert"),
                            ("health_reminder", "Health Reminder"),
                            ("wellness_tip", "Wellness Tip"),
                        ],
                        max_length=30,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("action_url", models.CharField(blank=True, max_length=500)),
                ("action_label", models.CharField(blank=True, max_length=100)),
                ("source_type", models.CharField(blank=True, max_length=50)),
                ("source_id", models.UUIDField(blank=True, null=True)),
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
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("is_dismissed", models.BooleanField(default=False)),
                ("dismissed_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("channels_sent", models.JSONField(default=list)),
            ],
            options={
                "db_table": "cymed_portal_notifications",
            },
        ),
        migrations.CreateModel(
            name="NotificationPreference",
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
                ("account_id", models.UUIDField(db_index=True, unique=True)),
                ("push_enabled", models.BooleanField(default=True)),
                ("email_enabled", models.BooleanField(default=True)),
                ("sms_enabled", models.BooleanField(default=True)),
                ("appointment_notifications", models.BooleanField(default=True)),
                ("lab_notifications", models.BooleanField(default=True)),
                ("prescription_notifications", models.BooleanField(default=True)),
                ("payment_notifications", models.BooleanField(default=True)),
                ("message_notifications", models.BooleanField(default=True)),
                ("health_tips", models.BooleanField(default=True)),
                ("quiet_hours_enabled", models.BooleanField(default=False)),
                ("quiet_hours_start", models.TimeField(blank=True, null=True)),
                ("quiet_hours_end", models.TimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_notification_preferences",
            },
        ),
        migrations.CreateModel(
            name="NotificationTemplate",
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
                ("code", models.CharField(max_length=50, unique=True)),
                ("notification_type", models.CharField(max_length=50)),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("push", "Push"),
                            ("email", "Email"),
                            ("sms", "SMS"),
                            ("in_app", "In App"),
                        ],
                        default="push",
                        max_length=10,
                    ),
                ),
                ("language", models.CharField(default="en", max_length=10)),
                ("title_template", models.CharField(max_length=255)),
                ("body_template", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_portal_notification_templates",
            },
        ),
        migrations.CreateModel(
            name="PushSubscription",
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
                ("device_id", models.UUIDField(blank=True, null=True)),
                ("push_token", models.CharField(db_index=True, max_length=500)),
                (
                    "platform",
                    models.CharField(
                        choices=[
                            ("ios", "iOS"),
                            ("android", "Android"),
                            ("web", "Web"),
                        ],
                        default="android",
                        max_length=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_push_subscriptions",
            },
        ),
        migrations.AddIndex(
            model_name="patientnotification",
            index=models.Index(
                fields=["account_id", "is_read", "notification_type"],
                name="cymed_portal_notif_acct_read_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patientnotification",
            index=models.Index(
                fields=["account_id", "priority", "created_at"],
                name="cymed_portal_notif_acct_prio_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="pushsubscription",
            index=models.Index(
                fields=["account_id", "is_active"], name="cymed_portal_push_acct_active_idx"
            ),
        ),
    ]
