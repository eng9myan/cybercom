import django.utils.timezone
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProviderSchedule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_type", models.CharField(max_length=100)),
                ("provider_name", models.CharField(max_length=255)),
                ("unit_id", models.UUIDField(blank=True, null=True)),
                ("unit_name", models.CharField(blank=True, max_length=255)),
                ("department", models.CharField(blank=True, max_length=255)),
                ("schedule_date", models.DateField(db_index=True)),
                ("shift_type", models.CharField(
                    choices=[
                        ("morning", "Morning"),
                        ("afternoon", "Afternoon"),
                        ("evening", "Evening"),
                        ("night", "Night"),
                        ("on_call", "On Call"),
                        ("administrative", "Administrative"),
                    ],
                    default="morning",
                    max_length=30,
                )),
                ("shift_start", models.TimeField()),
                ("shift_end", models.TimeField()),
                ("status", models.CharField(
                    choices=[
                        ("scheduled", "Scheduled"),
                        ("confirmed", "Confirmed"),
                        ("swapped", "Swapped"),
                        ("cancelled", "Cancelled"),
                        ("completed", "Completed"),
                    ],
                    default="scheduled",
                    max_length=30,
                )),
                ("cycom_schedule_id", models.UUIDField(blank=True, null=True)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_prov_schedules"},
        ),
        migrations.CreateModel(
            name="ShiftAssignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("schedule", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="assignments",
                    to="cymed_provider_workforce.providerschedule",
                )),
                ("original_provider_id", models.UUIDField()),
                ("covering_provider_id", models.UUIDField()),
                ("assignment_type", models.CharField(
                    choices=[
                        ("regular", "Regular"),
                        ("swap", "Swap"),
                        ("coverage", "Coverage"),
                        ("float", "Float"),
                    ],
                    default="regular",
                    max_length=30,
                )),
                ("approved_by", models.UUIDField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("is_approved", models.BooleanField(default=False)),
                ("reason", models.TextField(blank=True)),
            ],
            options={"db_table": "cymed_prov_shift_assignments"},
        ),
        migrations.CreateModel(
            name="LeaveRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("leave_type", models.CharField(
                    choices=[
                        ("annual", "Annual"),
                        ("sick", "Sick"),
                        ("emergency", "Emergency"),
                        ("unpaid", "Unpaid"),
                        ("maternity", "Maternity"),
                        ("paternity", "Paternity"),
                        ("study", "Study"),
                        ("conference", "Conference"),
                        ("sabbatical", "Sabbatical"),
                    ],
                    max_length=30,
                )),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("total_days", models.PositiveSmallIntegerField()),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("approved", "Approved"),
                        ("rejected", "Rejected"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("reason", models.TextField(blank=True)),
                ("approved_by", models.UUIDField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("rejection_reason", models.TextField(blank=True)),
                ("cycom_leave_id", models.UUIDField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_leave_requests"},
        ),
        migrations.CreateModel(
            name="AttendanceRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("attendance_date", models.DateField(db_index=True)),
                ("check_in_time", models.TimeField(blank=True, null=True)),
                ("check_out_time", models.TimeField(blank=True, null=True)),
                ("actual_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("status", models.CharField(
                    choices=[
                        ("present", "Present"),
                        ("absent", "Absent"),
                        ("late", "Late"),
                        ("early_leave", "Early Leave"),
                        ("on_leave", "On Leave"),
                        ("off_day", "Off Day"),
                    ],
                    default="present",
                    max_length=20,
                )),
                ("cycom_attendance_id", models.UUIDField(blank=True, null=True)),
            ],
            options={"db_table": "cymed_prov_attendance"},
        ),
        migrations.CreateModel(
            name="CredentialExpiry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("provider_id", models.UUIDField(db_index=True)),
                ("provider_name", models.CharField(max_length=255)),
                ("credential_type", models.CharField(
                    choices=[
                        ("medical_license", "Medical License"),
                        ("board_certification", "Board Certification"),
                        ("bls", "BLS"),
                        ("acls", "ACLS"),
                        ("pals", "PALS"),
                        ("atls", "ATLS"),
                        ("specialty_certification", "Specialty Certification"),
                        ("dea_registration", "DEA Registration"),
                        ("malpractice_insurance", "Malpractice Insurance"),
                        ("npi_registration", "NPI Registration"),
                        ("other", "Other"),
                    ],
                    max_length=50,
                )),
                ("credential_name", models.CharField(max_length=255)),
                ("credential_number", models.CharField(blank=True, max_length=100)),
                ("issuing_authority", models.CharField(blank=True, max_length=255)),
                ("issued_date", models.DateField(blank=True, null=True)),
                ("expiry_date", models.DateField(db_index=True)),
                ("days_until_expiry", models.SmallIntegerField(blank=True, null=True)),
                ("alert_status", models.CharField(
                    choices=[
                        ("valid", "Valid"),
                        ("expiring_soon", "Expiring Soon"),
                        ("expired", "Expired"),
                    ],
                    default="valid",
                    max_length=20,
                )),
                ("is_acknowledged", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_prov_credential_expiry"},
        ),
        migrations.AddIndex(
            model_name="providerschedule",
            index=models.Index(fields=["tenant_id", "provider_id", "schedule_date"], name="cymed_prov_sched_tid_pid_date_idx"),
        ),
        migrations.AddIndex(
            model_name="providerschedule",
            index=models.Index(fields=["tenant_id", "unit_id", "schedule_date"], name="cymed_prov_sched_tid_uid_date_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="attendancerecord",
            unique_together={("tenant_id", "provider_id", "attendance_date")},
        ),
        migrations.AddIndex(
            model_name="credentialexpiry",
            index=models.Index(fields=["tenant_id", "provider_id", "expiry_date"], name="cymed_prov_cred_tid_pid_exp_idx"),
        ),
        migrations.AddIndex(
            model_name="credentialexpiry",
            index=models.Index(fields=["tenant_id", "alert_status"], name="cymed_prov_cred_tid_alert_idx"),
        ),
    ]
