import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PayerContract",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("insurance_company_id", models.UUIDField(db_index=True)),
                ("contract_name", models.CharField(max_length=200)),
                ("contract_number", models.CharField(max_length=100, unique=True, null=True, blank=True)),
                ("contract_type", models.CharField(max_length=30, choices=[("fee_for_service", "Fee for Service"), ("capitation", "Capitation"), ("bundled", "Bundled Payment"), ("drg", "DRG"), ("per_diem", "Per Diem"), ("value_based", "Value-Based"), ("discount_from_charges", "Discount from Charges")])),
                ("facility_id", models.UUIDField(null=True, blank=True)),
                ("effective_date", models.DateField()),
                ("expiry_date", models.DateField(null=True, blank=True)),
                ("status", models.CharField(max_length=20, default="draft", choices=[("draft", "Draft"), ("active", "Active"), ("expired", "Expired"), ("terminated", "Terminated"), ("pending_renewal", "Pending Renewal")])),
                ("base_discount_percentage", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ("notes", models.TextField(blank=True)),
                ("auto_renewal", models.BooleanField(default=False)),
                ("renewal_notice_days", models.PositiveSmallIntegerField(default=90)),
            ],
            options={"db_table": "cymed_rcm_ctr_contracts", "ordering": ["-effective_date"]},
        ),
        migrations.CreateModel(
            name="ContractRate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("contract", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rates", to="cymed_rcm_contracts.payercontract")),
                ("service_code", models.CharField(max_length=50)),
                ("service_description", models.CharField(max_length=500, blank=True)),
                ("rate_type", models.CharField(max_length=20, choices=[("flat_fee", "Flat Fee"), ("percentage", "Percentage"), ("per_diem", "Per Diem"), ("case_rate", "Case Rate"), ("drg", "DRG")])),
                ("rate_amount", models.DecimalField(max_digits=12, decimal_places=2)),
                ("rate_percentage", models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)),
                ("effective_date", models.DateField()),
                ("expiry_date", models.DateField(null=True, blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_rcm_ctr_rates", "ordering": ["service_code"]},
        ),
        migrations.CreateModel(
            name="ContractRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("contract", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rules", to="cymed_rcm_contracts.payercontract")),
                ("rule_type", models.CharField(max_length=30, choices=[("preauth_required", "Preauth Required"), ("timely_filing", "Timely Filing"), ("coordination_of_benefits", "Coordination of Benefits"), ("billing_restriction", "Billing Restriction"), ("exclusion", "Exclusion"), ("bundling", "Bundling"), ("global_period", "Global Period")])),
                ("rule_description", models.TextField()),
                ("applies_to_service_codes", models.JSONField(default=list)),
                ("days_limit", models.PositiveIntegerField(null=True, blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_rcm_ctr_rules", "ordering": ["rule_type"]},
        ),
        migrations.CreateModel(
            name="ReimbursementRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("contract", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reimbursement_rules", to="cymed_rcm_contracts.payercontract")),
                ("rule_name", models.CharField(max_length=200)),
                ("calculation_method", models.CharField(max_length=30, choices=[("percent_of_charges", "Percent of Charges"), ("fixed_rate", "Fixed Rate"), ("drg_multiplier", "DRG Multiplier"), ("case_rate", "Case Rate"), ("capitation", "Capitation")])),
                ("base_rate", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ("percentage_rate", models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)),
                ("applies_to_categories", models.JSONField(default=list)),
                ("max_reimbursement", models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_rcm_ctr_reimbursement_rules", "ordering": ["rule_name"]},
        ),
    ]
