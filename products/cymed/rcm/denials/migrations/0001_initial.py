import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DenialReason",
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
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("denial_code", models.CharField(max_length=50, unique=True)),
                ("description", models.CharField(max_length=500)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("eligibility", "Eligibility"),
                            ("authorization", "Authorization"),
                            ("medical_necessity", "Medical Necessity"),
                            ("coding", "Coding"),
                            ("documentation", "Documentation"),
                            ("duplicate", "Duplicate"),
                            ("timely_filing", "Timely Filing"),
                            ("network", "Network"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("common_resolution", models.TextField(blank=True)),
                (
                    "appeal_success_rate",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_rcm_denial_reasons",
                "ordering": ["denial_code"],
            },
        ),
        migrations.CreateModel(
            name="Denial",
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
                ("claim_id", models.UUIDField(db_index=True)),
                ("claim_line_id", models.UUIDField(blank=True, null=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("insurance_plan_id", models.UUIDField(db_index=True)),
                ("denial_date", models.DateField()),
                ("denial_code", models.CharField(max_length=50)),
                (
                    "denial_category",
                    models.CharField(
                        choices=[
                            ("eligibility", "Eligibility"),
                            ("authorization", "Authorization"),
                            ("medical_necessity", "Medical Necessity"),
                            ("coding", "Coding"),
                            ("documentation", "Documentation"),
                            ("duplicate", "Duplicate"),
                            ("timely_filing", "Timely Filing"),
                            ("network", "Network"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("denial_description", models.TextField()),
                (
                    "denial_amount",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("in_review", "In Review"),
                            ("appealing", "Appealing"),
                            ("resolved", "Resolved"),
                            ("written_off", "Written Off"),
                        ],
                        default="open",
                        max_length=20,
                    ),
                ),
                (
                    "root_cause",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("missing_auth", "Missing Authorization"),
                            ("wrong_code", "Wrong Code"),
                            ("expired_coverage", "Expired Coverage"),
                            ("missing_docs", "Missing Documentation"),
                            ("wrong_provider", "Wrong Provider"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "assigned_to_user_id",
                    models.UUIDField(blank=True, null=True),
                ),
                ("ai_denial_prediction", models.BooleanField(default=False)),
                (
                    "ai_prediction_confidence",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
            ],
            options={
                "db_table": "cymed_rcm_denial_denials",
                "ordering": ["-denial_date", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Appeal",
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
                    "denial",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="appeals",
                        to="cymed_rcm_denials.denial",
                    ),
                ),
                (
                    "appeal_level",
                    models.PositiveSmallIntegerField(default=1),
                ),
                ("appeal_date", models.DateField()),
                ("submitted_by_user_id", models.UUIDField()),
                (
                    "appeal_type",
                    models.CharField(
                        choices=[
                            ("internal", "Internal"),
                            ("external", "External"),
                            ("peer_review", "Peer Review"),
                            ("administrative", "Administrative"),
                            ("legal", "Legal"),
                        ],
                        max_length=20,
                    ),
                ),
                ("appeal_reason", models.TextField()),
                ("supporting_documents", models.JSONField(default=list)),
                ("clinical_justification", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("under_review", "Under Review"),
                            ("upheld", "Upheld"),
                            ("overturned", "Overturned"),
                            ("partially_overturned", "Partially Overturned"),
                            ("withdrawn", "Withdrawn"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("deadline_date", models.DateField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_denial_appeals",
                "ordering": ["-appeal_date", "appeal_level"],
            },
        ),
        migrations.CreateModel(
            name="AppealOutcome",
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
                    "appeal",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outcome",
                        to="cymed_rcm_denials.appeal",
                    ),
                ),
                ("outcome_date", models.DateField()),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("approved", "Approved"),
                            ("partially_approved", "Partially Approved"),
                            ("denied", "Denied"),
                            ("withdrawn", "Withdrawn"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "recovered_amount",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=12
                    ),
                ),
                ("outcome_notes", models.TextField(blank=True)),
                ("payer_reference", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "db_table": "cymed_rcm_denial_appeal_outcomes",
                "ordering": ["-outcome_date"],
            },
        ),
        migrations.CreateModel(
            name="CorrectiveAction",
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
                    "denial",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="corrective_actions",
                        to="cymed_rcm_denials.denial",
                    ),
                ),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("resubmit_with_auth", "Resubmit with Authorization"),
                            ("add_documentation", "Add Documentation"),
                            ("recode", "Recode"),
                            ("correct_patient_info", "Correct Patient Info"),
                            ("resubmit_in_network", "Resubmit In-Network"),
                            ("write_off", "Write Off"),
                        ],
                        max_length=30,
                    ),
                ),
                ("description", models.TextField()),
                ("assigned_to_user_id", models.UUIDField()),
                ("due_date", models.DateField(blank=True, null=True)),
                (
                    "completed_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
            ],
            options={
                "db_table": "cymed_rcm_denial_corrective_actions",
                "ordering": ["-created_at"],
            },
        ),
    ]
