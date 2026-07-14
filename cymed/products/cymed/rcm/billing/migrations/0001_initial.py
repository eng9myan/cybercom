import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PatientAccount",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("account_number", models.CharField(max_length=50, unique=True)),
                (
                    "account_status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("inactive", "Inactive"),
                            ("suspended", "Suspended"),
                            ("closed", "Closed"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("guarantor_patient_id", models.UUIDField(blank=True, null=True)),
                (
                    "guarantor_type",
                    models.CharField(
                        choices=[
                            ("self", "Self"),
                            ("parent", "Parent"),
                            ("spouse", "Spouse"),
                            ("employer", "Employer"),
                            ("government", "Government"),
                            ("other", "Other"),
                        ],
                        default="self",
                        max_length=20,
                    ),
                ),
                ("primary_insurance_member_id", models.UUIDField(blank=True, null=True)),
                ("secondary_insurance_member_id", models.UUIDField(blank=True, null=True)),
                ("tertiary_insurance_member_id", models.UUIDField(blank=True, null=True)),
                ("credit_balance", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                (
                    "outstanding_balance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                ("fhir_account_id", models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_bill_patient_accounts",
                "ordering": ["-created_at"],
                "unique_together": {("tenant_id", "patient_id")},
            },
        ),
        migrations.CreateModel(
            name="EncounterBilling",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "patient_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="encounter_billings",
                        to="cymed_rcm_billing.patientaccount",
                    ),
                ),
                ("encounter_id", models.UUIDField(db_index=True)),
                (
                    "encounter_type",
                    models.CharField(
                        choices=[
                            ("outpatient", "Outpatient"),
                            ("inpatient", "Inpatient"),
                            ("emergency", "Emergency"),
                            ("day_case", "Day Case"),
                            ("telemedicine", "Telemedicine"),
                            ("home_visit", "Home Visit"),
                            ("lab", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("pharmacy", "Pharmacy"),
                        ],
                        max_length=30,
                    ),
                ),
                ("encounter_date", models.DateField()),
                ("facility_id", models.UUIDField(db_index=True)),
                ("attending_provider_id", models.UUIDField(db_index=True)),
                ("department_id", models.UUIDField(blank=True, null=True)),
                (
                    "billing_status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("coded", "Coded"),
                            ("reviewed", "Reviewed"),
                            ("billed", "Billed"),
                            ("paid", "Paid"),
                            ("partial", "Partial"),
                            ("denied", "Denied"),
                            ("written_off", "Written Off"),
                        ],
                        default="open",
                        max_length=20,
                    ),
                ),
                ("total_charges", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                (
                    "insurance_expected",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                (
                    "patient_responsibility",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                ("amount_paid", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("balance_due", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("icd11_primary_diagnosis", models.CharField(blank=True, max_length=20)),
                ("icd11_secondary_diagnoses", models.JSONField(default=list)),
            ],
            options={
                "db_table": "cymed_rcm_bill_encounter_billings",
                "ordering": ["-encounter_date"],
                "unique_together": {("tenant_id", "encounter_id")},
            },
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "patient_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoices",
                        to="cymed_rcm_billing.patientaccount",
                    ),
                ),
                (
                    "encounter_billing",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="invoices",
                        to="cymed_rcm_billing.encounterbilling",
                    ),
                ),
                ("invoice_number", models.CharField(max_length=50, unique=True)),
                (
                    "invoice_type",
                    models.CharField(
                        choices=[
                            ("patient", "Patient"),
                            ("insurance", "Insurance"),
                            ("corporate", "Corporate"),
                            ("government", "Government"),
                        ],
                        max_length=20,
                    ),
                ),
                ("invoice_date", models.DateField()),
                ("due_date", models.DateField()),
                ("billing_party_id", models.UUIDField(blank=True, null=True)),
                (
                    "billing_party_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("insurance", "Insurance"),
                            ("corporate", "Corporate"),
                            ("government", "Government"),
                            ("self_pay", "Self Pay"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("issued", "Issued"),
                            ("sent", "Sent"),
                            ("partial", "Partial"),
                            ("paid", "Paid"),
                            ("overdue", "Overdue"),
                            ("cancelled", "Cancelled"),
                            ("written_off", "Written Off"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "amount_subtotal",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                ("amount_tax", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                (
                    "amount_discount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                ("amount_total", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("amount_paid", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                (
                    "amount_outstanding",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                ("currency", models.CharField(default="SAR", max_length=3)),
                ("notes", models.TextField(blank=True)),
                ("fhir_invoice_id", models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_bill_invoices",
                "ordering": ["-invoice_date"],
            },
        ),
        migrations.CreateModel(
            name="InvoiceLine",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="cymed_rcm_billing.invoice",
                    ),
                ),
                ("line_number", models.PositiveSmallIntegerField(default=1)),
                ("service_date", models.DateField()),
                ("service_code", models.CharField(max_length=50)),
                ("service_description", models.CharField(max_length=500)),
                ("quantity", models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ("unit_price", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                (
                    "discount_percentage",
                    models.DecimalField(decimal_places=2, default=0, max_digits=5),
                ),
                (
                    "discount_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                ("line_total", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("tax_amount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("charge_id", models.UUIDField(blank=True, null=True)),
                ("icd11_diagnosis_code", models.CharField(blank=True, max_length=20)),
            ],
            options={
                "db_table": "cymed_rcm_bill_invoice_lines",
                "ordering": ["line_number"],
            },
        ),
        migrations.CreateModel(
            name="BillingAdjustment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adjustments",
                        to="cymed_rcm_billing.invoice",
                    ),
                ),
                (
                    "adjustment_type",
                    models.CharField(
                        choices=[
                            ("contractual", "Contractual"),
                            ("write_off", "Write Off"),
                            ("discount", "Discount"),
                            ("refund", "Refund"),
                            ("correction", "Correction"),
                            ("insurance_writeoff", "Insurance Write-Off"),
                            ("bad_debt", "Bad Debt"),
                            ("courtesy", "Courtesy"),
                        ],
                        max_length=30,
                    ),
                ),
                ("adjustment_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("adjustment_date", models.DateField(auto_now_add=True)),
                ("reason", models.TextField(blank=True)),
                ("approved_by_user_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_bill_adjustments",
                "ordering": ["-adjustment_date"],
            },
        ),
        migrations.CreateModel(
            name="Refund",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="refunds",
                        to="cymed_rcm_billing.invoice",
                    ),
                ),
                ("refund_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "refund_method",
                    models.CharField(
                        choices=[
                            ("cash", "Cash"),
                            ("card", "Card"),
                            ("bank_transfer", "Bank Transfer"),
                            ("cheque", "Cheque"),
                            ("credit_note", "Credit Note"),
                            ("insurance_reversal", "Insurance Reversal"),
                        ],
                        max_length=20,
                    ),
                ),
                ("refund_date", models.DateField()),
                ("reason", models.TextField(blank=True)),
                ("processed_by_user_id", models.UUIDField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("processed", "Processed"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
            ],
            options={
                "db_table": "cymed_rcm_bill_refunds",
                "ordering": ["-refund_date"],
            },
        ),
    ]
