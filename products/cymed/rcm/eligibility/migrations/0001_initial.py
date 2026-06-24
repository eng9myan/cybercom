import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EligibilityRequest",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("insurance_plan_id", models.UUIDField(db_index=True)),
                ("insurance_member_id", models.UUIDField(null=True, blank=True)),
                ("service_date", models.DateField()),
                (
                    "service_type",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("medical", "Medical"),
                            ("pharmacy", "Pharmacy"),
                            ("dental", "Dental"),
                            ("vision", "Vision"),
                            ("mental_health", "Mental Health"),
                            ("substance_abuse", "Substance Abuse"),
                            ("preventive", "Preventive"),
                            ("emergency", "Emergency"),
                        ],
                    ),
                ),
                (
                    "request_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("real_time", "Real-Time"),
                            ("batch", "Batch"),
                        ],
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        default="pending",
                        choices=[
                            ("pending", "Pending"),
                            ("submitted", "Submitted"),
                            ("received", "Received"),
                            ("error", "Error"),
                        ],
                    ),
                ),
                ("fhir_coverage_eligibility_request_id", models.CharField(max_length=200, blank=True, null=True)),
                ("payer_transaction_id", models.CharField(max_length=200, blank=True, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_elig_requests",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CoverageVerification",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("insurance_plan_id", models.UUIDField(db_index=True)),
                ("encounter_id", models.UUIDField(null=True, blank=True)),
                ("verified_by_user_id", models.UUIDField(null=True, blank=True)),
                ("verified_at", models.DateTimeField(null=True, blank=True)),
                (
                    "verification_method",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("electronic", "Electronic"),
                            ("phone", "Phone"),
                            ("portal", "Portal"),
                            ("manual", "Manual"),
                        ],
                    ),
                ),
                ("coverage_confirmed", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_coverage_verifications",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="EligibilityResponse",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "eligibility_request",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response",
                        to="cymed_rcm_eligibility.eligibilityrequest",
                    ),
                ),
                ("is_eligible", models.BooleanField(default=False)),
                (
                    "coverage_status",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("active", "Active"),
                            ("inactive", "Inactive"),
                            ("pending", "Pending"),
                            ("unknown", "Unknown"),
                        ],
                    ),
                ),
                ("coverage_start_date", models.DateField(null=True, blank=True)),
                ("coverage_end_date", models.DateField(null=True, blank=True)),
                ("deductible_amount", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ("deductible_met", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ("out_of_pocket_max", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ("out_of_pocket_met", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ("copay_amount", models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)),
                ("coinsurance_percentage", models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)),
                ("patient_responsibility_estimate", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ("raw_response", models.JSONField(default=dict)),
                ("fhir_coverage_eligibility_response_id", models.CharField(max_length=200, blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_elig_responses",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="BenefitVerification",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "coverage_verification",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="benefit_verifications",
                        to="cymed_rcm_eligibility.coverageverification",
                    ),
                ),
                (
                    "benefit_type",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("hospitalization", "Hospitalization"),
                            ("outpatient", "Outpatient"),
                            ("emergency", "Emergency"),
                            ("surgery", "Surgery"),
                            ("lab", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("pharmacy", "Pharmacy"),
                            ("specialist", "Specialist"),
                            ("preventive", "Preventive"),
                            ("mental_health", "Mental Health"),
                            ("physical_therapy", "Physical Therapy"),
                            ("other", "Other"),
                        ],
                    ),
                ),
                ("is_covered", models.BooleanField(default=False)),
                ("requires_preauth", models.BooleanField(default=False)),
                ("coverage_percentage", models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)),
                ("copay", models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)),
                (
                    "network_status",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("in_network", "In-Network"),
                            ("out_of_network", "Out-of-Network"),
                            ("unknown", "Unknown"),
                        ],
                    ),
                ),
                ("benefit_notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_benefit_verifications",
                "ordering": ["benefit_type"],
            },
        ),
        migrations.AddIndex(
            model_name="eligibilityrequest",
            index=models.Index(fields=["tenant_id", "patient_id"], name="cymed_rcm_elig_req_tenant_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="eligibilityrequest",
            index=models.Index(fields=["tenant_id", "status"], name="cymed_rcm_elig_req_tenant_status_idx"),
        ),
        migrations.AddIndex(
            model_name="eligibilityrequest",
            index=models.Index(fields=["tenant_id", "service_date"], name="cymed_rcm_elig_req_tenant_svcdate_idx"),
        ),
        migrations.AddIndex(
            model_name="coverageverification",
            index=models.Index(fields=["tenant_id", "patient_id"], name="cymed_rcm_cov_ver_tenant_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="coverageverification",
            index=models.Index(fields=["tenant_id", "encounter_id"], name="cymed_rcm_cov_ver_tenant_enc_idx"),
        ),
    ]
