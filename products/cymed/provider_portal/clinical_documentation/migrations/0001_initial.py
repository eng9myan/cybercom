import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DocumentationTemplate",
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
                ("name", models.CharField(max_length=255)),
                (
                    "template_type",
                    models.CharField(
                        choices=[
                            ("soap", "SOAP"),
                            ("progress", "Progress"),
                            ("consult", "Consult"),
                            ("procedure", "Procedure"),
                            ("discharge", "Discharge"),
                            ("nursing", "Nursing"),
                            ("operative", "Operative"),
                            ("transfer", "Transfer"),
                            ("referral", "Referral"),
                            ("custom", "Custom"),
                        ],
                        max_length=20,
                    ),
                ),
                ("specialty", models.CharField(blank=True, max_length=100)),
                ("content_template", models.TextField()),
                ("smart_phrases", models.JSONField(default=list)),
                ("created_by_provider_id", models.UUIDField()),
                ("is_shared", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("usage_count", models.PositiveIntegerField(default=0)),
                ("version", models.CharField(default="1.0", max_length=20)),
            ],
            options={
                "db_table": "cymed_prov_doc_templates",
            },
        ),
        migrations.CreateModel(
            name="SmartPhrase",
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
                ("code", models.CharField(max_length=100)),
                ("expansion", models.TextField()),
                (
                    "phrase_type",
                    models.CharField(
                        choices=[
                            ("phrase", "Phrase"),
                            ("abbreviation", "Abbreviation"),
                            ("template_block", "Template Block"),
                        ],
                        default="phrase",
                        max_length=20,
                    ),
                ),
                ("created_by_provider_id", models.UUIDField()),
                ("is_personal", models.BooleanField(default=True)),
                ("specialty", models.CharField(blank=True, max_length=100)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "cymed_prov_smart_phrases",
            },
        ),
        migrations.CreateModel(
            name="ProviderClinicalNote",
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
                ("patient_id", models.UUIDField(db_index=True)),
                ("cymed_encounter_id", models.UUIDField(blank=True, null=True)),
                ("author_provider_id", models.UUIDField(db_index=True)),
                ("author_name", models.CharField(max_length=255)),
                ("author_type", models.CharField(max_length=100)),
                (
                    "note_type",
                    models.CharField(
                        choices=[
                            ("soap", "SOAP"),
                            ("progress", "Progress"),
                            ("consult", "Consult"),
                            ("procedure", "Procedure"),
                            ("discharge", "Discharge"),
                            ("nursing", "Nursing"),
                            ("addendum", "Addendum"),
                            ("operative", "Operative"),
                            ("transfer", "Transfer"),
                            ("referral", "Referral"),
                        ],
                        max_length=20,
                    ),
                ),
                ("note_title", models.CharField(blank=True, max_length=500)),
                ("note_body", models.TextField()),
                ("template_id", models.UUIDField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("in_review", "In Review"),
                            ("signed", "Signed"),
                            ("amended", "Amended"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("signed_at", models.DateTimeField(blank=True, null=True)),
                ("signed_by", models.UUIDField(blank=True, null=True)),
                ("amended_at", models.DateTimeField(blank=True, null=True)),
                ("amendment_reason", models.TextField(blank=True)),
                ("cymed_document_id", models.UUIDField(blank=True, null=True)),
                ("fhir_composition_id", models.CharField(blank=True, max_length=255)),
                ("is_confidential", models.BooleanField(default=False)),
                ("ai_summary", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_prov_clinical_notes",
            },
        ),
        migrations.CreateModel(
            name="NoteCoSignature",
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
                    "note",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cosignatures",
                        to="cymed_provider_clinical_documentation.providerclinicalnote",
                    ),
                ),
                ("cosigner_provider_id", models.UUIDField()),
                ("cosigner_name", models.CharField(max_length=255)),
                ("cosigner_type", models.CharField(max_length=100)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("supervisor", "Supervisor"),
                            ("attending", "Attending"),
                            ("cosigner", "Cosigner"),
                        ],
                        max_length=20,
                    ),
                ),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("signed_at", models.DateTimeField(blank=True, null=True)),
                ("is_signed", models.BooleanField(default=False)),
                ("rejection_reason", models.TextField(blank=True)),
            ],
            options={
                "db_table": "cymed_prov_note_cosignatures",
            },
        ),
        migrations.CreateModel(
            name="VoiceDictation",
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
                    "note",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dictations",
                        to="cymed_provider_clinical_documentation.providerclinicalnote",
                    ),
                ),
                ("provider_id", models.UUIDField()),
                ("audio_url", models.URLField(blank=True)),
                ("transcript_text", models.TextField(blank=True)),
                ("ai_transcript", models.TextField(blank=True)),
                ("duration_seconds", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("recording", "Recording"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="recording",
                        max_length=20,
                    ),
                ),
                ("integration_provider", models.CharField(blank=True, max_length=255)),
            ],
            options={
                "db_table": "cymed_prov_voice_dictations",
            },
        ),
        migrations.AddConstraint(
            model_name="smartphrase",
            constraint=models.UniqueConstraint(
                fields=["tenant_id", "created_by_provider_id", "code"],
                name="unique_smart_phrase_per_provider",
            ),
        ),
        migrations.AddIndex(
            model_name="providerclinicalnote",
            index=models.Index(
                fields=["tenant_id", "patient_id", "note_type"],
                name="cymed_prov_cn_tenant_patient_type_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="providerclinicalnote",
            index=models.Index(
                fields=["tenant_id", "author_provider_id", "status"],
                name="cymed_prov_cn_tenant_author_status_idx",
            ),
        ),
    ]
