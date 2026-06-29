import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CareTeam",
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
                ("team_name", models.CharField(max_length=255)),
                (
                    "team_type",
                    models.CharField(
                        choices=[
                            ("primary", "Primary"),
                            ("specialty", "Specialty"),
                            ("multidisciplinary", "Multidisciplinary"),
                            ("on_call", "On Call"),
                            ("rapid_response", "Rapid Response"),
                            ("perioperative", "Perioperative"),
                            ("maternity", "Maternity"),
                            ("oncology", "Oncology"),
                            ("custom", "Custom"),
                        ],
                        max_length=20,
                    ),
                ),
                ("patient_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("unit_id", models.UUIDField(blank=True, null=True)),
                ("specialty", models.CharField(blank=True, max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("created_by_provider_id", models.UUIDField()),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_prov_care_teams",
            },
        ),
        migrations.CreateModel(
            name="CareTeamMember",
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
                    "care_team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members",
                        to="cymed_provider_care_team.careteam",
                    ),
                ),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("provider_type", models.CharField(max_length=100)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("attending", "Attending"),
                            ("resident", "Resident"),
                            ("intern", "Intern"),
                            ("charge_nurse", "Charge Nurse"),
                            ("nurse", "Nurse"),
                            ("pharmacist", "Pharmacist"),
                            ("therapist", "Therapist"),
                            ("social_worker", "Social Worker"),
                            ("care_coordinator", "Care Coordinator"),
                            ("consultant", "Consultant"),
                            ("student", "Student"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_primary", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("left_at", models.DateTimeField(blank=True, null=True)),
                ("added_by", models.UUIDField()),
            ],
            options={
                "db_table": "cymed_prov_care_team_members",
            },
        ),
        migrations.CreateModel(
            name="CareTeamAssignment",
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
                    "care_team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="patient_assignments",
                        to="cymed_provider_care_team.careteam",
                    ),
                ),
                ("patient_id", models.UUIDField(db_index=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("unassigned_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("assignment_reason", models.TextField(blank=True)),
                ("assigned_by", models.UUIDField()),
            ],
            options={
                "db_table": "cymed_prov_care_team_assignments",
            },
        ),
        migrations.CreateModel(
            name="CareTeamRole",
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
                ("role_code", models.CharField(max_length=50, unique=True)),
                ("role_name", models.CharField(max_length=255)),
                (
                    "role_type",
                    models.CharField(
                        choices=[
                            ("physician", "Physician"),
                            ("nursing", "Nursing"),
                            ("pharmacy", "Pharmacy"),
                            ("allied_health", "Allied Health"),
                            ("administrative", "Administrative"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("responsibilities", models.JSONField(default=list)),
                ("can_order", models.BooleanField(default=False)),
                ("can_sign_documents", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_prov_care_team_roles",
            },
        ),
        migrations.CreateModel(
            name="CoverageSchedule",
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
                    "care_team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="coverage_schedules",
                        to="cymed_provider_care_team.careteam",
                    ),
                ),
                ("covering_provider_id", models.UUIDField(db_index=True)),
                ("covering_provider_name", models.CharField(max_length=255)),
                ("covered_provider_id", models.UUIDField()),
                ("coverage_date", models.DateField(db_index=True)),
                ("coverage_start", models.TimeField()),
                ("coverage_end", models.TimeField()),
                (
                    "coverage_type",
                    models.CharField(
                        choices=[
                            ("on_call", "On Call"),
                            ("cross_cover", "Cross Cover"),
                            ("holiday", "Holiday"),
                            ("leave_cover", "Leave Cover"),
                        ],
                        default="on_call",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_prov_coverage_schedules",
            },
        ),
        migrations.AddConstraint(
            model_name="careteammember",
            constraint=models.UniqueConstraint(
                fields=["tenant_id", "care_team", "provider_id"],
                name="unique_care_team_member_per_team",
            ),
        ),
    ]
