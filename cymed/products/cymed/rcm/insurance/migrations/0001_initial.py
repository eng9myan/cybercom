import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="InsuranceCompany",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("short_name", models.CharField(max_length=50)),
                (
                    "company_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("private", "Private"),
                            ("government", "Government"),
                            ("semi_government", "Semi-Government"),
                            ("cooperative", "Cooperative"),
                            ("international", "International"),
                        ],
                    ),
                ),
                ("payer_id", models.CharField(max_length=50, unique=True)),
                ("country", models.CharField(max_length=3, default="SAU")),
                ("is_active", models.BooleanField(default=True)),
                ("contact_phone", models.CharField(max_length=30, blank=True)),
                ("contact_email", models.EmailField(blank=True)),
                ("portal_url", models.CharField(max_length=500, blank=True)),
                ("eligibility_endpoint", models.CharField(max_length=500, blank=True)),
                ("claims_endpoint", models.CharField(max_length=500, blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_ins_companies",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="InsurancePlan",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="plans",
                        to="cymed_rcm_insurance.insurancecompany",
                    ),
                ),
                ("plan_name", models.CharField(max_length=200)),
                ("plan_code", models.CharField(max_length=50)),
                (
                    "plan_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("hmo", "HMO"),
                            ("ppo", "PPO"),
                            ("epo", "EPO"),
                            ("pos", "POS"),
                            ("indemnity", "Indemnity"),
                            ("government", "Government"),
                            ("corporate", "Corporate"),
                            ("family", "Family"),
                            ("individual", "Individual"),
                        ],
                    ),
                ),
                (
                    "network_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("in_network", "In-Network"),
                            ("out_of_network", "Out-of-Network"),
                            ("both", "Both"),
                        ],
                    ),
                ),
                (
                    "coverage_category",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("basic", "Basic"),
                            ("standard", "Standard"),
                            ("enhanced", "Enhanced"),
                            ("premium", "Premium"),
                            ("catastrophic", "Catastrophic"),
                        ],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("effective_date", models.DateField(null=True, blank=True)),
                ("expiry_date", models.DateField(null=True, blank=True)),
                (
                    "max_annual_benefit",
                    models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True),
                ),
            ],
            options={
                "db_table": "cymed_rcm_ins_plans",
                "ordering": ["company", "plan_name"],
            },
        ),
        migrations.CreateModel(
            name="InsuranceMember",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                (
                    "insurance_plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="members",
                        to="cymed_rcm_insurance.insuranceplan",
                    ),
                ),
                ("member_id", models.CharField(max_length=100)),
                ("group_number", models.CharField(max_length=100, blank=True)),
                (
                    "member_relationship",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("self", "Self"),
                            ("spouse", "Spouse"),
                            ("child", "Child"),
                            ("dependent", "Dependent"),
                            ("other", "Other"),
                        ],
                    ),
                ),
                ("is_primary_holder", models.BooleanField(default=True)),
                ("primary_holder_patient_id", models.UUIDField(null=True, blank=True)),
                ("effective_date", models.DateField()),
                ("expiry_date", models.DateField(null=True, blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("priority_order", models.PositiveSmallIntegerField(default=1)),
            ],
            options={
                "db_table": "cymed_rcm_ins_members",
                "ordering": ["patient_id", "priority_order"],
            },
        ),
        migrations.CreateModel(
            name="Coverage",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "insurance_member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="coverages",
                        to="cymed_rcm_insurance.insurancemember",
                    ),
                ),
                (
                    "coverage_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("medical", "Medical"),
                            ("dental", "Dental"),
                            ("vision", "Vision"),
                            ("pharmacy", "Pharmacy"),
                            ("mental_health", "Mental Health"),
                            ("maternity", "Maternity"),
                            ("rehabilitation", "Rehabilitation"),
                            ("other", "Other"),
                        ],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(null=True, blank=True)),
                (
                    "deductible_individual",
                    models.DecimalField(max_digits=12, decimal_places=2, default=0),
                ),
                (
                    "deductible_family",
                    models.DecimalField(max_digits=12, decimal_places=2, default=0),
                ),
                (
                    "out_of_pocket_individual",
                    models.DecimalField(max_digits=12, decimal_places=2, default=0),
                ),
                (
                    "out_of_pocket_family",
                    models.DecimalField(max_digits=12, decimal_places=2, default=0),
                ),
                ("fhir_coverage_id", models.CharField(max_length=200, blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_ins_coverages",
                "ordering": ["insurance_member", "coverage_type"],
            },
        ),
        migrations.CreateModel(
            name="Benefit",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "coverage",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="benefits",
                        to="cymed_rcm_insurance.coverage",
                    ),
                ),
                ("service_category", models.CharField(max_length=50)),
                (
                    "coverage_percentage",
                    models.DecimalField(max_digits=5, decimal_places=2, default=100),
                ),
                ("copay_amount", models.DecimalField(max_digits=8, decimal_places=2, default=0)),
                ("requires_preauth", models.BooleanField(default=False)),
                (
                    "annual_limit",
                    models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True),
                ),
                ("visit_limit", models.PositiveIntegerField(null=True, blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_ins_benefits",
                "ordering": ["coverage", "service_category"],
            },
        ),
        migrations.CreateModel(
            name="CoverageRule",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "insurance_plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="coverage_rules",
                        to="cymed_rcm_insurance.insuranceplan",
                    ),
                ),
                (
                    "rule_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("preauth_required", "Pre-Authorization Required"),
                            ("exclusion", "Exclusion"),
                            ("limitation", "Limitation"),
                            ("copay_waiver", "Copay Waiver"),
                            ("referral_required", "Referral Required"),
                            ("network_restriction", "Network Restriction"),
                        ],
                    ),
                ),
                ("service_code", models.CharField(max_length=50, blank=True)),
                ("rule_description", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_rcm_ins_coverage_rules",
                "ordering": ["insurance_plan", "rule_type"],
            },
        ),
        migrations.CreateModel(
            name="InsuranceCard",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "insurance_member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cards",
                        to="cymed_rcm_insurance.insurancemember",
                    ),
                ),
                ("card_front_url", models.CharField(max_length=500, blank=True)),
                ("card_back_url", models.CharField(max_length=500, blank=True)),
                ("issued_date", models.DateField(null=True, blank=True)),
                ("expiry_date", models.DateField(null=True, blank=True)),
                ("is_current", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_rcm_ins_cards",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="insurancemember",
            unique_together={("tenant_id", "patient_id", "insurance_plan", "priority_order")},
        ),
        migrations.AddIndex(
            model_name="insurancecompany",
            index=models.Index(
                fields=["tenant_id", "is_active"], name="cymed_rcm_ins_co_tenant_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="insurancecompany",
            index=models.Index(
                fields=["tenant_id", "company_type"], name="cymed_rcm_ins_co_tenant_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="insuranceplan",
            index=models.Index(
                fields=["tenant_id", "is_active"], name="cymed_rcm_ins_plan_tenant_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="insuranceplan",
            index=models.Index(
                fields=["tenant_id", "plan_type"], name="cymed_rcm_ins_plan_tenant_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="insurancemember",
            index=models.Index(
                fields=["tenant_id", "patient_id"], name="cymed_rcm_ins_mbr_tenant_patient_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="insurancemember",
            index=models.Index(
                fields=["tenant_id", "is_active"], name="cymed_rcm_ins_mbr_tenant_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="insurancemember",
            index=models.Index(
                fields=["tenant_id", "priority_order"], name="cymed_rcm_ins_mbr_tenant_priority_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coverage",
            index=models.Index(
                fields=["tenant_id", "coverage_type"], name="cymed_rcm_ins_cov_tenant_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coverage",
            index=models.Index(
                fields=["tenant_id", "is_active"], name="cymed_rcm_ins_cov_tenant_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coveragerule",
            index=models.Index(
                fields=["tenant_id", "rule_type"], name="cymed_rcm_ins_rule_tenant_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coveragerule",
            index=models.Index(
                fields=["tenant_id", "is_active"], name="cymed_rcm_ins_rule_tenant_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="insurancecard",
            index=models.Index(
                fields=["tenant_id", "is_current"], name="cymed_rcm_ins_card_tenant_curr_idx"
            ),
        ),
    ]
