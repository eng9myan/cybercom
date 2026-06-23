import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PatientList",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("name", models.CharField(max_length=255)),
                ("list_type", models.CharField(
                    choices=[
                        ("my_patients", "My Patients"),
                        ("ward", "Ward"),
                        ("clinic", "Clinic"),
                        ("emergency", "Emergency"),
                        ("icu", "ICU"),
                        ("shared_team", "Shared Team"),
                        ("custom", "Custom"),
                    ],
                    max_length=30,
                )),
                ("workspace_id", models.UUIDField(db_index=True)),
                ("unit_id", models.UUIDField(blank=True, null=True)),
                ("specialty", models.CharField(blank=True, max_length=255)),
                ("is_shared", models.BooleanField(default=False)),
                ("shared_with", models.JSONField(default=list)),
                ("auto_populate", models.BooleanField(default=True)),
                ("sort_order", models.CharField(
                    choices=[
                        ("name", "Name"),
                        ("bed_number", "Bed Number"),
                        ("admission_date", "Admission Date"),
                        ("acuity", "Acuity"),
                    ],
                    default="name",
                    max_length=30,
                )),
                ("patient_count", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_prov_patient_lists", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="PatientAssignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_list", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="assignments",
                    to="cymed_provider_patient_lists.patientlist",
                )),
                ("patient_id", models.UUIDField(db_index=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                ("bed_number", models.CharField(blank=True, max_length=50)),
                ("unit_name", models.CharField(blank=True, max_length=255)),
                ("admission_date", models.DateField(blank=True, null=True)),
                ("attending_provider_id", models.UUIDField(blank=True, null=True)),
                ("is_primary", models.BooleanField(default=True)),
                ("acuity_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("removed_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_prov_patient_assignments", "ordering": ["-added_at"]},
        ),
        migrations.CreateModel(
            name="ProviderAssignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_type", models.CharField(max_length=50)),
                ("role", models.CharField(
                    choices=[
                        ("attending", "Attending"),
                        ("covering", "Covering"),
                        ("consulting", "Consulting"),
                        ("primary_nurse", "Primary Nurse"),
                        ("charge_nurse", "Charge Nurse"),
                        ("resident", "Resident"),
                        ("intern", "Intern"),
                        ("co_attending", "Co-Attending"),
                    ],
                    max_length=30,
                )),
                ("unit_id", models.UUIDField(blank=True, null=True)),
                ("is_primary", models.BooleanField(default=True)),
                ("effective_from", models.DateTimeField()),
                ("effective_until", models.DateTimeField(blank=True, null=True)),
                ("coverage_type", models.CharField(
                    choices=[
                        ("scheduled", "Scheduled"),
                        ("on_call", "On Call"),
                        ("cross_cover", "Cross Cover"),
                    ],
                    default="scheduled",
                    max_length=30,
                )),
                ("assigned_by", models.UUIDField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_provider_assignments", "ordering": ["-effective_from"]},
        ),
        migrations.CreateModel(
            name="PatientCensus",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("unit_id", models.UUIDField(db_index=True)),
                ("unit_name", models.CharField(max_length=255)),
                ("census_date", models.DateField(db_index=True)),
                ("total_beds", models.PositiveIntegerField()),
                ("occupied_beds", models.PositiveIntegerField()),
                ("available_beds", models.PositiveIntegerField()),
                ("pending_admissions", models.PositiveIntegerField(default=0)),
                ("pending_discharges", models.PositiveIntegerField(default=0)),
                ("average_acuity", models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True)),
                ("by_provider", models.JSONField(default=dict)),
            ],
            options={"db_table": "cymed_prov_patient_census", "ordering": ["-census_date"]},
        ),
        migrations.AlterUniqueTogether(
            name="patientassignment",
            unique_together={("tenant_id", "patient_list", "patient_id")},
        ),
        migrations.AlterUniqueTogether(
            name="patientcensus",
            unique_together={("tenant_id", "unit_id", "census_date")},
        ),
        migrations.AddIndex(
            model_name="patientlist",
            index=models.Index(fields=["tenant_id", "workspace_id"], name="cymed_prov_plist_tenant_wkspc_idx"),
        ),
        migrations.AddIndex(
            model_name="patientlist",
            index=models.Index(fields=["tenant_id", "list_type", "is_active"], name="cymed_prov_plist_type_active_idx"),
        ),
        migrations.AddIndex(
            model_name="patientassignment",
            index=models.Index(fields=["tenant_id", "patient_id", "is_active"], name="cymed_prov_passign_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="providerassignment",
            index=models.Index(fields=["tenant_id", "patient_id", "provider_id"], name="cymed_prov_provassign_pat_prov_idx"),
        ),
        migrations.AddIndex(
            model_name="providerassignment",
            index=models.Index(fields=["tenant_id", "provider_id", "effective_from"], name="cymed_prov_provassign_prov_eff_idx"),
        ),
        migrations.AddIndex(
            model_name="patientcensus",
            index=models.Index(fields=["tenant_id", "unit_id", "census_date"], name="cymed_prov_census_unit_date_idx"),
        ),
    ]
