import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CollectionCase",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("patient_account_id", models.UUIDField(db_index=True)),
                ("case_number", models.CharField(max_length=50, unique=True)),
                (
                    "outstanding_balance",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                (
                    "original_balance",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                (
                    "aging_bucket",
                    models.CharField(
                        choices=[
                            ("current", "Current"),
                            ("30_days", "30 Days"),
                            ("60_days", "60 Days"),
                            ("90_days", "90 Days"),
                            ("120_days", "120 Days"),
                            ("over_120", "Over 120 Days"),
                        ],
                        default="current",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("payment_plan", "Payment Plan"),
                            ("legal", "Legal"),
                            ("written_off", "Written Off"),
                            ("resolved", "Resolved"),
                            ("closed", "Closed"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("critical", "Critical"),
                        ],
                        default="medium",
                        max_length=10,
                    ),
                ),
                (
                    "assigned_to_user_id",
                    models.UUIDField(blank=True, null=True),
                ),
                (
                    "last_contact_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "next_follow_up_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "ai_collection_risk_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_coll_cases",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CollectionAction",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "collection_case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actions",
                        to="cymed_rcm_collections.collectioncase",
                    ),
                ),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("phone_call", "Phone Call"),
                            ("sms", "SMS"),
                            ("email", "Email"),
                            ("letter", "Letter"),
                            ("payment_arrangement", "Payment Arrangement"),
                            ("legal_notice", "Legal Notice"),
                            ("field_visit", "Field Visit"),
                            ("payment_received", "Payment Received"),
                            ("plan_created", "Plan Created"),
                            ("write_off_recommended", "Write-Off Recommended"),
                        ],
                        max_length=30,
                    ),
                ),
                ("action_date", models.DateTimeField(auto_now_add=True)),
                ("performed_by_user_id", models.UUIDField()),
                ("notes", models.TextField(blank=True)),
                (
                    "amount_collected",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=12
                    ),
                ),
                (
                    "next_action_date",
                    models.DateField(blank=True, null=True),
                ),
            ],
            options={
                "db_table": "cymed_rcm_coll_actions",
                "ordering": ["-action_date"],
            },
        ),
        migrations.CreateModel(
            name="PaymentPlan",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "collection_case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payment_plans",
                        to="cymed_rcm_collections.collectioncase",
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                (
                    "installment_amount",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("weekly", "Weekly"),
                            ("biweekly", "Bi-Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        max_length=20,
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "number_of_installments",
                    models.PositiveSmallIntegerField(),
                ),
                (
                    "amount_paid",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=14
                    ),
                ),
                (
                    "amount_remaining",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("defaulted", "Defaulted"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "approved_by_user_id",
                    models.UUIDField(blank=True, null=True),
                ),
            ],
            options={
                "db_table": "cymed_rcm_coll_payment_plans",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CollectionOutcome",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "collection_case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outcomes",
                        to="cymed_rcm_collections.collectioncase",
                    ),
                ),
                ("outcome_date", models.DateField()),
                (
                    "outcome_type",
                    models.CharField(
                        choices=[
                            ("paid_in_full", "Paid in Full"),
                            ("partial_payment", "Partial Payment"),
                            ("payment_plan_completed", "Payment Plan Completed"),
                            ("written_off", "Written Off"),
                            ("legal_settlement", "Legal Settlement"),
                            ("uncollectable", "Uncollectable"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "amount_recovered",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=14
                    ),
                ),
                (
                    "amount_written_off",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=14
                    ),
                ),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_coll_outcomes",
                "ordering": ["-outcome_date"],
            },
        ),
    ]
