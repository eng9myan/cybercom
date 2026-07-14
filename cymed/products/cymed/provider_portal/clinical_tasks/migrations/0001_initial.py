import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ClinicalTask",
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
                    "task_type",
                    models.CharField(
                        choices=[
                            ("lab_follow_up", "Lab Follow-Up"),
                            ("imaging_follow_up", "Imaging Follow-Up"),
                            ("medication_review", "Medication Review"),
                            ("patient_callback", "Patient Callback"),
                            ("referral", "Referral"),
                            ("discharge_planning", "Discharge Planning"),
                            ("care_coordination", "Care Coordination"),
                            ("documentation", "Documentation"),
                            ("critical_result_review", "Critical Result Review"),
                            ("order_review", "Order Review"),
                            ("wound_care", "Wound Care"),
                            ("vital_signs", "Vital Signs"),
                            ("blood_glucose", "Blood Glucose"),
                            ("medication_administration", "Medication Administration"),
                            ("custom", "Custom"),
                        ],
                        max_length=50,
                    ),
                ),
                ("title", models.CharField(max_length=500)),
                ("description", models.TextField(blank=True)),
                ("patient_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("routine", "Routine"),
                            ("urgent", "Urgent"),
                            ("stat", "STAT"),
                            ("critical", "Critical"),
                        ],
                        default="routine",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                            ("escalated", "Escalated"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("assigned_to_provider_id", models.UUIDField(db_index=True)),
                ("assigned_to_type", models.CharField(max_length=50)),
                ("created_by_provider_id", models.UUIDField()),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("completed_by_provider_id", models.UUIDField(blank=True, null=True)),
                ("escalated_to_provider_id", models.UUIDField(blank=True, null=True)),
                ("escalated_at", models.DateTimeField(blank=True, null=True)),
                ("source_type", models.CharField(blank=True, max_length=100)),
                ("source_id", models.UUIDField(blank=True, null=True)),
                ("unit_id", models.UUIDField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_prov_tasks", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TaskAssignment",
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
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="cymed_provider_clinical_tasks.clinicaltask",
                    ),
                ),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_type", models.CharField(max_length=50)),
                ("assigned_by", models.UUIDField()),
                (
                    "assignment_type",
                    models.CharField(
                        choices=[
                            ("primary", "Primary"),
                            ("collaborator", "Collaborator"),
                            ("observer", "Observer"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_prov_task_assignments", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TaskComment",
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
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="cymed_provider_clinical_tasks.clinicaltask",
                    ),
                ),
                ("author_provider_id", models.UUIDField()),
                ("author_name", models.CharField(max_length=255)),
                ("comment_text", models.TextField()),
                ("is_system_comment", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_prov_task_comments", "ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="TaskEscalation",
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
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="escalations",
                        to="cymed_provider_clinical_tasks.clinicaltask",
                    ),
                ),
                ("escalated_by_provider_id", models.UUIDField()),
                ("escalated_to_provider_id", models.UUIDField()),
                ("escalation_reason", models.TextField()),
                ("previous_priority", models.CharField(max_length=20)),
                ("new_priority", models.CharField(max_length=20)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_task_escalations", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="clinicaltask",
            index=models.Index(
                fields=["tenant_id", "assigned_to_provider_id", "status"],
                name="cymed_prov_task_prov_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicaltask",
            index=models.Index(
                fields=["tenant_id", "patient_id", "status"],
                name="cymed_prov_task_patient_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicaltask",
            index=models.Index(
                fields=["tenant_id", "priority", "status"],
                name="cymed_prov_task_priority_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicaltask",
            index=models.Index(
                fields=["tenant_id", "due_at"], name="cymed_prov_task_tenant_due_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="taskassignment",
            index=models.Index(
                fields=["tenant_id", "task", "provider_id"],
                name="cymed_prov_taskassign_task_prov_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="taskcomment",
            index=models.Index(
                fields=["tenant_id", "task", "created_at"], name="cymed_prov_taskcomment_task_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="taskescalation",
            index=models.Index(fields=["tenant_id", "task"], name="cymed_prov_taskesc_task_idx"),
        ),
    ]
