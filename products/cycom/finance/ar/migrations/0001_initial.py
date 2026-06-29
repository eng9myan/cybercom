import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
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
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("name_ar", models.CharField(blank=True, max_length=200)),
                ("customer_code", models.CharField(max_length=50)),
                ("tax_id", models.CharField(blank=True, max_length=50)),
                (
                    "credit_limit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                ("payment_terms_days", models.IntegerField(default=30)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cycom_finance_ar_customers"},
        ),
        migrations.CreateModel(
            name="Invoice",
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
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("invoice_number", models.CharField(max_length=50)),
                ("invoice_date", models.DateField()),
                ("due_date", models.DateField()),
                (
                    "subtotal",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "tax_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "paid_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("sent", "Sent"),
                            ("partial", "Partial"),
                            ("paid", "Paid"),
                            ("overdue", "Overdue"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("currency", models.CharField(default="SAR", max_length=3)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoices",
                        to="cycom_finance_ar.customer",
                    ),
                ),
            ],
            options={"db_table": "cycom_finance_ar_invoices"},
        ),
        migrations.CreateModel(
            name="InvoiceLine",
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
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("description", models.CharField(max_length=500)),
                (
                    "quantity",
                    models.DecimalField(decimal_places=3, default=1, max_digits=10),
                ),
                (
                    "unit_price",
                    models.DecimalField(decimal_places=2, max_digits=18),
                ),
                (
                    "tax_rate",
                    models.DecimalField(decimal_places=2, default=0, max_digits=5),
                ),
                (
                    "line_total",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="cycom_finance_ar.invoice",
                    ),
                ),
            ],
            options={"db_table": "cycom_finance_ar_invoice_lines"},
        ),
        migrations.CreateModel(
            name="Payment",
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
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("payment_date", models.DateField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=18)),
                (
                    "method",
                    models.CharField(
                        choices=[
                            ("cash", "Cash"),
                            ("bank", "Bank Transfer"),
                            ("card", "Card"),
                            ("insurance", "Insurance"),
                            ("wallet", "Wallet"),
                        ],
                        max_length=20,
                    ),
                ),
                ("reference", models.CharField(blank=True, max_length=100)),
                ("notes", models.TextField(blank=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payments",
                        to="cycom_finance_ar.customer",
                    ),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="payments",
                        to="cycom_finance_ar.invoice",
                    ),
                ),
            ],
            options={"db_table": "cycom_finance_ar_payments"},
        ),
        migrations.CreateModel(
            name="ARAgingBucket",
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
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "bucket_label",
                    models.CharField(
                        choices=[
                            ("current", "Current"),
                            ("1-30", "1-30 Days"),
                            ("31-60", "31-60 Days"),
                            ("61-90", "61-90 Days"),
                            ("90+", "90+ Days"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=18),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="aging_buckets",
                        to="cycom_finance_ar.customer",
                    ),
                ),
            ],
            options={"db_table": "cycom_finance_ar_aging_buckets"},
        ),
    ]
