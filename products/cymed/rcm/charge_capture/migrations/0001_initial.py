import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Charge",
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
                ("encounter_id", models.UUIDField(db_index=True)),
                ("charge_date", models.DateField()),
                (
                    "service_source",
                    models.CharField(
                        choices=[
                            ("clinic", "Clinic"),
                            ("hospital", "Hospital"),
                            ("laboratory", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("pharmacy", "Pharmacy"),
                            ("emergency", "Emergency"),
                            ("or", "Operating Room"),
                            ("icu", "ICU"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "charge_category",
                    models.CharField(
                        choices=[
                            ("consultation", "Consultation"),
                            ("procedure", "Procedure"),
                            ("medication", "Medication"),
                            ("lab_test", "Lab Test"),
                            ("imaging", "Imaging"),
                            ("admission", "Admission"),
                            ("room_and_board", "Room and Board"),
                            ("nursing", "Nursing"),
                            ("anesthesia", "Anesthesia"),
                            ("therapy", "Therapy"),
                            ("supply", "Supply"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("service_code", models.CharField(max_length=50)),
                ("service_description", models.CharField(max_length=500)),
                ("icd11_diagnosis_code", models.CharField(blank=True, max_length=20)),
                ("quantity", models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ("unit_price", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("reviewed", "Reviewed"),
                            ("approved", "Approved"),
                            ("billed", "Billed"),
                            ("voided", "Voided"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("is_billable", models.BooleanField(default=True)),
                ("source_order_id", models.UUIDField(blank=True, null=True)),
                ("source_module", models.CharField(blank=True, max_length=50)),
                ("rendering_provider_id", models.UUIDField(blank=True, null=True)),
                ("facility_id", models.UUIDField(db_index=True)),
                ("encounter_billing_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_rcm_chg_charges",
                "ordering": ["-charge_date"],
            },
        ),
        migrations.CreateModel(
            name="ChargeItem",
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
                    "charge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="cymed_rcm_charge_capture.charge",
                    ),
                ),
                ("item_code", models.CharField(max_length=50)),
                ("item_description", models.CharField(max_length=500)),
                ("quantity", models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ("unit_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ],
            options={
                "db_table": "cymed_rcm_chg_charge_items",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="ChargeRule",
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
                ("rule_name", models.CharField(max_length=200)),
                (
                    "service_source",
                    models.CharField(
                        choices=[
                            ("clinic", "Clinic"),
                            ("hospital", "Hospital"),
                            ("laboratory", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("pharmacy", "Pharmacy"),
                            ("emergency", "Emergency"),
                            ("or", "Operating Room"),
                            ("icu", "ICU"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "charge_category",
                    models.CharField(
                        choices=[
                            ("consultation", "Consultation"),
                            ("procedure", "Procedure"),
                            ("medication", "Medication"),
                            ("lab_test", "Lab Test"),
                            ("imaging", "Imaging"),
                            ("admission", "Admission"),
                            ("room_and_board", "Room and Board"),
                            ("nursing", "Nursing"),
                            ("anesthesia", "Anesthesia"),
                            ("therapy", "Therapy"),
                            ("supply", "Supply"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("auto_generate", models.BooleanField(default=True)),
                ("trigger_event", models.CharField(max_length=50)),
                ("service_code_map", models.JSONField(default=dict)),
                ("multiplier", models.DecimalField(decimal_places=4, default=1, max_digits=8)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_rcm_chg_charge_rules",
                "ordering": ["rule_name"],
            },
        ),
        migrations.CreateModel(
            name="ChargeAdjustment",
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
                    "charge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adjustments",
                        to="cymed_rcm_charge_capture.charge",
                    ),
                ),
                (
                    "adjustment_type",
                    models.CharField(
                        choices=[
                            ("discount", "Discount"),
                            ("correction", "Correction"),
                            ("override", "Override"),
                            ("void", "Void"),
                            ("split", "Split"),
                        ],
                        max_length=30,
                    ),
                ),
                ("original_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("adjusted_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("reason", models.TextField(blank=True)),
                ("adjusted_by_user_id", models.UUIDField()),
            ],
            options={
                "db_table": "cymed_rcm_chg_adjustments",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ChargeAudit",
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
                    "charge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audits",
                        to="cymed_rcm_charge_capture.charge",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("modified", "Modified"),
                            ("approved", "Approved"),
                            ("voided", "Voided"),
                            ("billed", "Billed"),
                            ("reversed", "Reversed"),
                        ],
                        max_length=30,
                    ),
                ),
                ("performed_by_user_id", models.UUIDField()),
                ("previous_status", models.CharField(blank=True, max_length=20)),
                ("new_status", models.CharField(blank=True, max_length=20)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_rcm_chg_audits",
                "ordering": ["-created_at"],
            },
        ),
    ]
