import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProviderOrderRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                ("ordering_provider_id", models.UUIDField(db_index=True)),
                ("ordering_provider_name", models.CharField(max_length=255)),
                (
                    "order_category",
                    models.CharField(
                        choices=[
                            ("laboratory", "Laboratory"),
                            ("imaging", "Imaging"),
                            ("medication", "Medication"),
                            ("procedure", "Procedure"),
                            ("referral", "Referral"),
                            ("nursing", "Nursing"),
                            ("dietary", "Dietary"),
                            ("respiratory", "Respiratory"),
                            ("physical_therapy", "Physical Therapy"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("order_type", models.CharField(blank=True, max_length=100)),
                ("order_name", models.CharField(max_length=255)),
                ("order_details", models.JSONField(default=dict)),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("routine", "Routine"),
                            ("urgent", "Urgent"),
                            ("stat", "STAT"),
                        ],
                        default="routine",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("acknowledged", "Acknowledged"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                            ("on_hold", "On Hold"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("clinical_indication", models.TextField(blank=True)),
                ("fhir_service_request_id", models.CharField(blank=True, max_length=255)),
                ("fhir_medication_request_id", models.CharField(blank=True, max_length=255)),
                ("cymed_lab_order_id", models.UUIDField(blank=True, null=True)),
                ("cymed_imaging_order_id", models.UUIDField(blank=True, null=True)),
                ("cymed_rx_id", models.UUIDField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_order_requests"},
        ),
        migrations.CreateModel(
            name="OrderModification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="modifications",
                        to="cymed_provider_orders.providerorderrequest",
                    ),
                ),
                ("modified_by_provider_id", models.UUIDField()),
                ("modified_by_name", models.CharField(max_length=255)),
                (
                    "modification_type",
                    models.CharField(
                        choices=[
                            ("edit", "Edit"),
                            ("cancel", "Cancel"),
                            ("hold", "Hold"),
                            ("resume", "Resume"),
                            ("priority_change", "Priority Change"),
                        ],
                        max_length=30,
                    ),
                ),
                ("previous_value", models.JSONField(default=dict)),
                ("new_value", models.JSONField(default=dict)),
                ("reason", models.TextField()),
                ("is_applied", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_prov_order_modifications"},
        ),
        migrations.CreateModel(
            name="OrderStatusUpdate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_updates",
                        to="cymed_provider_orders.providerorderrequest",
                    ),
                ),
                ("previous_status", models.CharField(max_length=30)),
                ("new_status", models.CharField(max_length=30)),
                ("updated_by_provider_id", models.UUIDField(blank=True, null=True)),
                ("updated_by_name", models.CharField(blank=True, max_length=255)),
                ("updated_by_system", models.CharField(blank=True, max_length=255)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_prov_order_status_updates"},
        ),
        migrations.CreateModel(
            name="OrderSet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("specialty", models.CharField(blank=True, max_length=100)),
                (
                    "order_set_type",
                    models.CharField(
                        choices=[
                            ("admission", "Admission"),
                            ("discharge", "Discharge"),
                            ("procedure", "Procedure"),
                            ("condition_specific", "Condition Specific"),
                            ("custom", "Custom"),
                        ],
                        max_length=30,
                    ),
                ),
                ("orders", models.JSONField(default=list)),
                ("created_by_provider_id", models.UUIDField()),
                ("is_shared", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("usage_count", models.PositiveIntegerField(default=0)),
            ],
            options={"db_table": "cymed_prov_order_sets"},
        ),
        migrations.AddIndex(
            model_name="providerorderrequest",
            index=models.Index(
                fields=["tenant_id", "patient_id", "order_category"],
                name="cymed_prov_ord_tid_pid_cat_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="providerorderrequest",
            index=models.Index(
                fields=["tenant_id", "ordering_provider_id", "status"],
                name="cymed_prov_ord_tid_opid_sts_idx",
            ),
        ),
    ]
