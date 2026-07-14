import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Preauthorization",
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
                ("insurance_member_id", models.UUIDField(db_index=True)),
                ("insurance_plan_id", models.UUIDField(db_index=True)),
                ("encounter_id", models.UUIDField(null=True, blank=True)),
                (
                    "auth_number",
                    models.CharField(max_length=100, unique=True, null=True, blank=True),
                ),
                (
                    "authorization_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("service", "Service"),
                            ("procedure", "Procedure"),
                            ("medication", "Medication"),
                            ("imaging", "Imaging"),
                            ("hospitalization", "Hospitalization"),
                            ("home_health", "Home Health"),
                            ("dme", "Durable Medical Equipment"),
                            ("rehabilitation", "Rehabilitation"),
                        ],
                    ),
                ),
                ("service_description", models.CharField(max_length=500)),
                ("icd11_diagnosis_codes", models.JSONField(default=list)),
                ("requested_units", models.PositiveIntegerField(default=1)),
                ("approved_units", models.PositiveIntegerField(null=True, blank=True)),
                ("requested_start_date", models.DateField()),
                ("requested_end_date", models.DateField(null=True, blank=True)),
                ("approved_start_date", models.DateField(null=True, blank=True)),
                ("approved_end_date", models.DateField(null=True, blank=True)),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        default="draft",
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("pending_info", "Pending Information"),
                            ("approved", "Approved"),
                            ("partially_approved", "Partially Approved"),
                            ("denied", "Denied"),
                            ("expired", "Expired"),
                            ("cancelled", "Cancelled"),
                        ],
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        max_length=10,
                        default="routine",
                        choices=[("routine", "Routine"), ("urgent", "Urgent"), ("stat", "STAT")],
                    ),
                ),
                ("requesting_provider_id", models.UUIDField(db_index=True)),
                ("ordering_provider_id", models.UUIDField(null=True, blank=True)),
                ("facility_id", models.UUIDField(null=True, blank=True)),
                ("source_order_id", models.UUIDField(null=True, blank=True)),
                ("source_module", models.CharField(max_length=30, blank=True)),
            ],
            options={"db_table": "cymed_rcm_preauths", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AuthorizationRequest",
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
                    "preauthorization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="cymed_rcm_preauthorization.preauthorization",
                    ),
                ),
                ("request_date", models.DateTimeField(auto_now_add=True)),
                ("submitted_by_user_id", models.UUIDField()),
                ("clinical_notes", models.TextField(blank=True)),
                ("supporting_documents", models.JSONField(default=list)),
                ("payer_reference_number", models.CharField(max_length=200, blank=True, null=True)),
                (
                    "submission_method",
                    models.CharField(
                        max_length=20,
                        default="electronic",
                        choices=[
                            ("electronic", "Electronic"),
                            ("fax", "Fax"),
                            ("phone", "Phone"),
                            ("portal", "Portal"),
                        ],
                    ),
                ),
            ],
            options={"db_table": "cymed_rcm_auth_requests", "ordering": ["-request_date"]},
        ),
        migrations.CreateModel(
            name="AuthorizationDecision",
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
                    "preauthorization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="decisions",
                        to="cymed_rcm_preauthorization.preauthorization",
                    ),
                ),
                (
                    "decision",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("approved", "Approved"),
                            ("partially_approved", "Partially Approved"),
                            ("denied", "Denied"),
                            ("pending_info", "Pending Information"),
                            ("referred_to_committee", "Referred to Committee"),
                        ],
                    ),
                ),
                ("decision_date", models.DateTimeField()),
                ("decided_by_payer_user", models.CharField(max_length=200, blank=True)),
                ("approval_notes", models.TextField(blank=True)),
                ("denial_reason_code", models.CharField(max_length=50, blank=True)),
                ("denial_reason_description", models.TextField(blank=True)),
                ("conditions", models.TextField(blank=True)),
                ("effective_date", models.DateField(null=True, blank=True)),
                ("expiry_date", models.DateField(null=True, blank=True)),
            ],
            options={"db_table": "cymed_rcm_auth_decisions", "ordering": ["-decision_date"]},
        ),
        migrations.CreateModel(
            name="AuthorizationAppeal",
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
                    "preauthorization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="appeals",
                        to="cymed_rcm_preauthorization.preauthorization",
                    ),
                ),
                ("appeal_date", models.DateTimeField(auto_now_add=True)),
                ("submitted_by_user_id", models.UUIDField()),
                ("appeal_reason", models.TextField()),
                ("supporting_documents", models.JSONField(default=list)),
                ("appeal_level", models.PositiveSmallIntegerField(default=1)),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("submitted", "Submitted"),
                            ("under_review", "Under Review"),
                            ("approved", "Approved"),
                            ("denied", "Denied"),
                            ("withdrawn", "Withdrawn"),
                        ],
                    ),
                ),
                ("outcome_date", models.DateTimeField(null=True, blank=True)),
                ("outcome_notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_rcm_auth_appeals", "ordering": ["-appeal_date"]},
        ),
    ]
