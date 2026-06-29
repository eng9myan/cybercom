import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "tenant_id",
                    models.UUIDField(db_index=True, editable=False),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                ("code", models.CharField(max_length=20)),
                ("name", models.CharField(max_length=200)),
                ("name_ar", models.CharField(blank=True, max_length=200)),
                (
                    "account_type",
                    models.CharField(
                        choices=[
                            ("asset", "Asset"),
                            ("liability", "Liability"),
                            ("equity", "Equity"),
                            ("revenue", "Revenue"),
                            ("expense", "Expense"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("currency", models.CharField(default="SAR", max_length=3)),
                (
                    "balance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "parent_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="children",
                        to="cycom_finance_gl.account",
                    ),
                ),
            ],
            options={
                "db_table": "cycom_finance_gl_accounts",
            },
        ),
        migrations.CreateModel(
            name="JournalEntry",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "tenant_id",
                    models.UUIDField(db_index=True, editable=False),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                ("entry_date", models.DateField()),
                ("description", models.TextField(blank=True)),
                ("reference", models.CharField(blank=True, max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("posted", "Posted"),
                            ("reversed", "Reversed"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("posted_by", models.UUIDField(blank=True, null=True)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "total_debit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "total_credit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
            ],
            options={
                "db_table": "cycom_finance_gl_journal_entries",
            },
        ),
        migrations.CreateModel(
            name="JournalLine",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "tenant_id",
                    models.UUIDField(db_index=True, editable=False),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "debit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "credit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                ("description", models.CharField(blank=True, max_length=500)),
                ("cost_center", models.CharField(blank=True, max_length=100)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="journal_lines",
                        to="cycom_finance_gl.account",
                    ),
                ),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="cycom_finance_gl.journalentry",
                    ),
                ),
            ],
            options={
                "db_table": "cycom_finance_gl_journal_lines",
            },
        ),
    ]
