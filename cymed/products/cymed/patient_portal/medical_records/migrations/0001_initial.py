import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MedicalRecordAccess",
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
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                (
                    "record_type",
                    models.CharField(
                        choices=[
                            ("diagnosis", "Diagnosis"),
                            ("condition", "Condition"),
                            ("allergy", "Allergy"),
                            ("immunization", "Immunization"),
                            ("care_plan", "Care Plan"),
                            ("clinical_note", "Clinical Note"),
                            ("discharge_summary", "Discharge Summary"),
                            ("visit_history", "Visit History"),
                            ("document", "Document"),
                        ],
                        max_length=30,
                    ),
                ),
                ("record_id", models.UUIDField(db_index=True)),
                (
                    "access_type",
                    models.CharField(
                        choices=[("view", "View"), ("download", "Download"), ("share", "Share")],
                        default="view",
                        max_length=20,
                    ),
                ),
                ("accessed_at", models.DateTimeField(auto_now_add=True)),
                ("access_context", models.CharField(blank=True, max_length=100)),
            ],
            options={
                "db_table": "cymed_portal_record_access",
            },
        ),
        migrations.CreateModel(
            name="SharedRecord",
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
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("record_type", models.CharField(max_length=50)),
                ("record_id", models.UUIDField()),
                ("record_title", models.CharField(max_length=255)),
                (
                    "shared_with_type",
                    models.CharField(
                        choices=[
                            ("provider", "Provider"),
                            ("family_member", "Family Member"),
                            ("employer", "Employer"),
                            ("insurer", "Insurer"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("shared_with_name", models.CharField(blank=True, max_length=255)),
                ("shared_with_email", models.EmailField(blank=True)),
                ("share_token", models.CharField(db_index=True, max_length=255, unique=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("is_password_protected", models.BooleanField(default=False)),
                ("access_count", models.PositiveIntegerField(default=0)),
                ("max_access_count", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("is_revoked", models.BooleanField(default=False)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_shared_records",
            },
        ),
        migrations.CreateModel(
            name="RecordDownloadHistory",
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
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                ("record_type", models.CharField(max_length=50)),
                ("record_id", models.UUIDField()),
                ("record_title", models.CharField(max_length=255)),
                (
                    "download_format",
                    models.CharField(
                        choices=[
                            ("pdf", "PDF"),
                            ("json", "JSON"),
                            ("fhir", "FHIR"),
                            ("csv", "CSV"),
                        ],
                        default="pdf",
                        max_length=10,
                    ),
                ),
                ("downloaded_at", models.DateTimeField(auto_now_add=True)),
                ("file_size_bytes", models.PositiveBigIntegerField(default=0)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                "db_table": "cymed_portal_download_history",
            },
        ),
        migrations.CreateModel(
            name="PatientDocument",
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
                ("account_id", models.UUIDField(db_index=True)),
                ("patient_id", models.UUIDField(db_index=True)),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("report", "Report"),
                            ("prescription", "Prescription"),
                            ("insurance_card", "Insurance Card"),
                            ("id_document", "ID Document"),
                            ("lab_result", "Lab Result"),
                            ("imaging", "Imaging"),
                            ("referral", "Referral"),
                            ("discharge_summary", "Discharge Summary"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("file_name", models.CharField(max_length=255)),
                ("file_url", models.URLField(max_length=2000)),
                ("file_size_bytes", models.PositiveBigIntegerField(default=0)),
                ("file_type", models.CharField(max_length=50)),
                ("document_date", models.DateField(blank=True, null=True)),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("uploaded_by_patient", "Uploaded by Patient"),
                            ("received_from_provider", "Received from Provider"),
                            ("generated_by_system", "Generated by System"),
                        ],
                        default="uploaded_by_patient",
                        max_length=30,
                    ),
                ),
                ("provider_name", models.CharField(blank=True, max_length=255)),
                ("is_shared", models.BooleanField(default=False)),
                ("tags", models.JSONField(default=list)),
            ],
            options={
                "db_table": "cymed_portal_patient_documents",
            },
        ),
        migrations.AddIndex(
            model_name="medicalrecordaccess",
            index=models.Index(
                fields=["account_id", "record_type"], name="cymed_rec_access_acct_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="medicalrecordaccess",
            index=models.Index(
                fields=["patient_id", "accessed_at"], name="cymed_rec_access_patient_date_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="sharedrecord",
            index=models.Index(
                fields=["account_id", "is_revoked"], name="cymed_shared_rec_acct_revoked_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="recorddownloadhistory",
            index=models.Index(
                fields=["account_id", "downloaded_at"], name="cymed_dl_hist_acct_date_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="patientdocument",
            index=models.Index(
                fields=["account_id", "document_type"], name="cymed_patient_doc_acct_type_idx"
            ),
        ),
    ]
