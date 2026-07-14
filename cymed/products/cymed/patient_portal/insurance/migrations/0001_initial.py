import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="InsuranceCard",
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
                ("insurer_name", models.CharField(max_length=255)),
                ("insurer_name_ar", models.CharField(blank=True, max_length=255)),
                ("policy_number", models.CharField(db_index=True, max_length=100)),
                ("member_id", models.CharField(max_length=100)),
                ("group_number", models.CharField(blank=True, max_length=100)),
                ("plan_name", models.CharField(blank=True, max_length=255)),
                (
                    "plan_type",
                    models.CharField(
                        choices=[
                            ("individual", "Individual"),
                            ("family", "Family"),
                            ("corporate", "Corporate"),
                            ("government", "Government"),
                        ],
                        default="individual",
                        max_length=20,
                    ),
                ),
                ("card_front_url", models.URLField(blank=True, max_length=2000)),
                ("card_back_url", models.URLField(blank=True, max_length=2000)),
                ("effective_date", models.DateField(blank=True, null=True)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("is_primary", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                ("coverage_details", models.JSONField(default=dict)),
                ("copay_details", models.JSONField(default=dict)),
                (
                    "deductible",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                (
                    "out_of_pocket_max",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
            ],
            options={
                "db_table": "cymed_portal_insurance_cards",
            },
        ),
        migrations.CreateModel(
            name="CoverageVerification",
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
                    "insurance_card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verifications",
                        to="cymed_portal_insurance.insurancecard",
                    ),
                ),
                (
                    "verification_type",
                    models.CharField(
                        choices=[
                            ("eligibility", "Eligibility"),
                            ("benefits", "Benefits"),
                            ("specific_service", "Specific Service"),
                        ],
                        default="eligibility",
                        max_length=20,
                    ),
                ),
                ("service_type", models.CharField(blank=True, max_length=100)),
                ("service_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("verified", "Verified"),
                            ("not_covered", "Not Covered"),
                            ("partially_covered", "Partially Covered"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("coverage_percentage", models.PositiveSmallIntegerField(blank=True, null=True)),
                (
                    "patient_responsibility",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                ("verification_details", models.JSONField(default=dict)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_coverage_verifications",
            },
        ),
        migrations.CreateModel(
            name="PreauthorizationRequest",
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
                    "insurance_card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preauths",
                        to="cymed_portal_insurance.insurancecard",
                    ),
                ),
                ("service_type", models.CharField(max_length=100)),
                ("service_description", models.TextField()),
                ("provider_name", models.CharField(blank=True, max_length=255)),
                ("provider_id", models.UUIDField(blank=True, null=True)),
                ("service_date", models.DateField(blank=True, null=True)),
                ("diagnosis_codes", models.JSONField(default=list)),
                ("procedure_codes", models.JSONField(default=list)),
                (
                    "estimated_cost",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("under_review", "Under Review"),
                            ("approved", "Approved"),
                            ("denied", "Denied"),
                            ("pending_info", "Pending Info"),
                            ("expired", "Expired"),
                        ],
                        default="submitted",
                        max_length=20,
                    ),
                ),
                ("auth_number", models.CharField(blank=True, max_length=100)),
                (
                    "approved_amount",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                ("denial_reason", models.TextField(blank=True)),
                ("valid_from", models.DateField(blank=True, null=True)),
                ("valid_until", models.DateField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_preauth_requests",
            },
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
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                (
                    "insurance_card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="claims",
                        to="cymed_portal_insurance.insurancecard",
                    ),
                ),
                ("claim_number", models.CharField(db_index=True, max_length=100)),
                ("service_date", models.DateField()),
                ("service_type", models.CharField(blank=True, max_length=100)),
                ("provider_name", models.CharField(blank=True, max_length=255)),
                ("billed_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "allowed_amount",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                (
                    "paid_amount",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                (
                    "patient_responsibility",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("processing", "Processing"),
                            ("paid", "Paid"),
                            ("denied", "Denied"),
                            ("appealing", "Appealing"),
                            ("closed", "Closed"),
                        ],
                        default="submitted",
                        max_length=20,
                    ),
                ),
                ("denial_reason", models.TextField(blank=True)),
                ("eob_url", models.URLField(blank=True, max_length=2000)),
            ],
            options={
                "db_table": "cymed_portal_claims",
            },
        ),
        migrations.AddIndex(
            model_name="insurancecard",
            index=models.Index(
                fields=["account_id", "is_active", "is_primary"],
                name="cymed_portal_ins_card_acct_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="coverageverification",
            index=models.Index(
                fields=["account_id", "status"], name="cymed_portal_cov_ver_acct_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="preauthorizationrequest",
            index=models.Index(
                fields=["account_id", "status"], name="cymed_portal_preauth_acct_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="claimstatus",
            index=models.Index(
                fields=["account_id", "status", "service_date"], name="cymed_portal_claim_acct_idx"
            ),
        ),
    ]
