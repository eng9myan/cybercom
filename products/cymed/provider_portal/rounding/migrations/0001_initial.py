import django.utils.timezone
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ClinicalRound",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("round_type", models.CharField(
                    choices=[
                        ("ward", "Ward"),
                        ("icu", "ICU"),
                        ("multidisciplinary", "Multidisciplinary"),
                        ("virtual", "Virtual"),
                        ("nursing", "Nursing"),
                        ("pharmacy", "Pharmacy"),
                        ("administrative", "Administrative"),
                    ],
                    max_length=30,
                )),
                ("round_name", models.CharField(blank=True, max_length=255)),
                ("unit_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("unit_name", models.CharField(blank=True, max_length=255)),
                ("attending_provider_id", models.UUIDField()),
                ("attending_name", models.CharField(max_length=255)),
                ("round_date", models.DateField(db_index=True)),
                ("scheduled_time", models.TimeField(blank=True, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(
                    choices=[
                        ("scheduled", "Scheduled"),
                        ("in_progress", "In Progress"),
                        ("completed", "Completed"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="scheduled",
                    max_length=20,
                )),
                ("patient_count", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_prov_rounds"},
        ),
        migrations.CreateModel(
            name="RoundTeam",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("round", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="team_members",
                    to="cymed_provider_rounding.clinicalround",
                )),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("provider_type", models.CharField(max_length=100)),
                ("role", models.CharField(
                    choices=[
                        ("attending", "Attending"),
                        ("resident", "Resident"),
                        ("intern", "Intern"),
                        ("nurse", "Nurse"),
                        ("pharmacist", "Pharmacist"),
                        ("therapist", "Therapist"),
                        ("social_worker", "Social Worker"),
                        ("student", "Student"),
                        ("observer", "Observer"),
                    ],
                    max_length=30,
                )),
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("is_present", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_prov_round_teams"},
        ),
        migrations.CreateModel(
            name="RoundChecklist",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("round", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="checklists",
                    to="cymed_provider_rounding.clinicalround",
                )),
                ("patient_id", models.UUIDField(db_index=True)),
                ("patient_name", models.CharField(blank=True, max_length=255)),
                ("bed_number", models.CharField(blank=True, max_length=50)),
                ("checklist_items", models.JSONField(default=list)),
                ("completed_items", models.PositiveIntegerField(default=0)),
                ("total_items", models.PositiveIntegerField(default=0)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_round_checklists"},
        ),
        migrations.CreateModel(
            name="RoundFinding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("round", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="findings",
                    to="cymed_provider_rounding.clinicalround",
                )),
                ("patient_id", models.UUIDField(db_index=True)),
                ("finding_type", models.CharField(
                    choices=[
                        ("clinical_observation", "Clinical Observation"),
                        ("vital_sign_concern", "Vital Sign Concern"),
                        ("medication_issue", "Medication Issue"),
                        ("imaging_result", "Imaging Result"),
                        ("lab_result", "Lab Result"),
                        ("care_plan_update", "Care Plan Update"),
                        ("discharge_planning", "Discharge Planning"),
                        ("other", "Other"),
                    ],
                    max_length=40,
                )),
                ("finding_text", models.TextField()),
                ("severity", models.CharField(
                    choices=[
                        ("routine", "Routine"),
                        ("notable", "Notable"),
                        ("urgent", "Urgent"),
                        ("critical", "Critical"),
                    ],
                    default="routine",
                    max_length=20,
                )),
                ("recorded_by_provider_id", models.UUIDField()),
                ("recorded_by_name", models.CharField(max_length=255)),
                ("requires_action", models.BooleanField(default=False)),
                ("is_resolved", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_prov_round_findings"},
        ),
        migrations.CreateModel(
            name="RoundAction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("round", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="actions",
                    to="cymed_provider_rounding.clinicalround",
                )),
                ("finding", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="actions",
                    to="cymed_provider_rounding.roundfinding",
                )),
                ("patient_id", models.UUIDField(db_index=True)),
                ("action_type", models.CharField(
                    choices=[
                        ("order_placed", "Order Placed"),
                        ("task_created", "Task Created"),
                        ("note_written", "Note Written"),
                        ("referral_sent", "Referral Sent"),
                        ("medication_adjusted", "Medication Adjusted"),
                        ("discharge_initiated", "Discharge Initiated"),
                        ("family_notified", "Family Notified"),
                        ("other", "Other"),
                    ],
                    max_length=40,
                )),
                ("action_description", models.TextField()),
                ("assigned_to_provider_id", models.UUIDField(blank=True, null=True)),
                ("assigned_to_name", models.CharField(blank=True, max_length=255)),
                ("due_by", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("completed", "Completed"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_round_actions"},
        ),
    ]
