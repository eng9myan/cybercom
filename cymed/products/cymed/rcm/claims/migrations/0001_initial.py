import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Claim",
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
                ("claim_number", models.CharField(max_length=50, unique=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("insurance_member_id", models.UUIDField(db_index=True)),
                ("insurance_plan_id", models.UUIDField(db_index=True)),
                ("encounter_billing_id", models.UUIDField(db_index=True)),
                (
                    "claim_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("institutional", "Institutional"),
                            ("professional", "Professional"),
                            ("dental", "Dental"),
                            ("pharmacy", "Pharmacy"),
                        ],
                    ),
                ),
                ("claim_date", models.DateField()),
                ("service_from_date", models.DateField()),
                ("service_to_date", models.DateField()),
                ("facility_id", models.UUIDField(db_index=True)),
                ("rendering_provider_id", models.UUIDField()),
                ("referring_provider_id", models.UUIDField(null=True, blank=True)),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        default="draft",
                        choices=[
                            ("draft", "Draft"),
                            ("ready", "Ready"),
                            ("submitted", "Submitted"),
                            ("acknowledged", "Acknowledged"),
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("partial", "Partial"),
                            ("denied", "Denied"),
                            ("voided", "Voided"),
                            ("resubmitted", "Resubmitted"),
                        ],
                    ),
                ),
                (
                    "total_billed_amount",
                    models.DecimalField(max_digits=14, decimal_places=2, default=0),
                ),
                (
                    "total_approved_amount",
                    models.DecimalField(max_digits=14, decimal_places=2, default=0),
                ),
                (
                    "total_paid_amount",
                    models.DecimalField(max_digits=14, decimal_places=2, default=0),
                ),
                (
                    "patient_responsibility",
                    models.DecimalField(max_digits=14, decimal_places=2, default=0),
                ),
                ("icd11_primary_diagnosis", models.CharField(max_length=20, blank=True)),
                ("icd11_secondary_diagnoses", models.JSONField(default=list)),
                ("preauthorization_number", models.CharField(max_length=100, blank=True)),
                ("preauthorization_id", models.UUIDField(null=True, blank=True)),
                ("is_resubmission", models.BooleanField(default=False)),
                ("original_claim_id", models.UUIDField(null=True, blank=True)),
                ("fhir_claim_id", models.CharField(max_length=200, blank=True, null=True)),
            ],
            options={"db_table": "cymed_rcm_clm_claims", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ClaimLine",
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
                    "claim",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="cymed_rcm_claims.claim",
                    ),
                ),
                ("line_number", models.PositiveSmallIntegerField()),
                ("service_date", models.DateField()),
                ("service_code", models.CharField(max_length=50)),
                ("service_description", models.CharField(max_length=500)),
                ("icd11_diagnosis_code", models.CharField(max_length=20, blank=True)),
                ("quantity", models.DecimalField(max_digits=10, decimal_places=2, default=1)),
                ("unit_charge", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("line_charge", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                (
                    "approved_amount",
                    models.DecimalField(max_digits=12, decimal_places=2, default=0),
                ),
                ("paid_amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                (
                    "line_status",
                    models.CharField(
                        max_length=20,
                        default="included",
                        choices=[
                            ("included", "Included"),
                            ("excluded", "Excluded"),
                            ("denied", "Denied"),
                            ("pending", "Pending"),
                        ],
                    ),
                ),
                ("denial_reason_code", models.CharField(max_length=50, blank=True)),
                ("rendering_provider_id", models.UUIDField(null=True, blank=True)),
                ("charge_id", models.UUIDField(null=True, blank=True)),
            ],
            options={"db_table": "cymed_rcm_clm_lines", "ordering": ["line_number"]},
        ),
        migrations.CreateModel(
            name="ClaimSubmission",
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
                    "claim",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to="cymed_rcm_claims.claim",
                    ),
                ),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("submitted_by_user_id", models.UUIDField()),
                (
                    "submission_method",
                    models.CharField(
                        max_length=20,
                        default="electronic",
                        choices=[
                            ("electronic", "Electronic"),
                            ("batch", "Batch"),
                            ("portal", "Portal"),
                            ("direct", "Direct"),
                        ],
                    ),
                ),
                ("payer_transaction_id", models.CharField(max_length=200, blank=True, null=True)),
                ("batch_id", models.CharField(max_length=200, blank=True, null=True)),
                ("acknowledgement_received", models.BooleanField(default=False)),
                ("acknowledgement_at", models.DateTimeField(null=True, blank=True)),
            ],
            options={"db_table": "cymed_rcm_clm_submissions", "ordering": ["-submitted_at"]},
        ),
        migrations.CreateModel(
            name="ClaimResponse",
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
                    "claim",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="cymed_rcm_claims.claim",
                    ),
                ),
                ("response_date", models.DateTimeField()),
                (
                    "response_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("acknowledgement", "Acknowledgement"),
                            ("payment", "Payment"),
                            ("denial", "Denial"),
                            ("additional_info_request", "Additional Info Request"),
                            ("partial_payment", "Partial Payment"),
                        ],
                    ),
                ),
                ("payer_claim_number", models.CharField(max_length=200, blank=True)),
                (
                    "approved_amount",
                    models.DecimalField(max_digits=14, decimal_places=2, default=0),
                ),
                ("paid_amount", models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ("payment_date", models.DateField(null=True, blank=True)),
                ("payment_method", models.CharField(max_length=30, blank=True)),
                ("eob_number", models.CharField(max_length=200, blank=True)),
                ("denial_codes", models.JSONField(default=list)),
                ("remarks", models.TextField(blank=True)),
                ("raw_response", models.JSONField(default=dict)),
                ("fhir_claim_response_id", models.CharField(max_length=200, blank=True, null=True)),
                ("fhir_eob_id", models.CharField(max_length=200, blank=True, null=True)),
            ],
            options={"db_table": "cymed_rcm_clm_responses", "ordering": ["-response_date"]},
        ),
        migrations.CreateModel(
            name="ClaimStatus",
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
                    "claim",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="cymed_rcm_claims.claim",
                    ),
                ),
                ("previous_status", models.CharField(max_length=20)),
                ("new_status", models.CharField(max_length=20)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("changed_by_user_id", models.UUIDField(null=True, blank=True)),
                ("notes", models.CharField(max_length=500, blank=True)),
            ],
            options={"db_table": "cymed_rcm_clm_status_history", "ordering": ["-changed_at"]},
        ),
        migrations.CreateModel(
            name="ClaimAttachment",
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
                    "claim",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="cymed_rcm_claims.claim",
                    ),
                ),
                (
                    "attachment_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("medical_record", "Medical Record"),
                            ("lab_result", "Lab Result"),
                            ("imaging", "Imaging"),
                            ("authorization", "Authorization"),
                            ("referral", "Referral"),
                            ("notes", "Notes"),
                            ("invoice", "Invoice"),
                            ("other", "Other"),
                        ],
                    ),
                ),
                ("file_url", models.CharField(max_length=500)),
                ("file_name", models.CharField(max_length=200)),
                ("uploaded_by_user_id", models.UUIDField()),
                ("is_required", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_rcm_clm_attachments", "ordering": ["-created_at"]},
        ),
    ]
