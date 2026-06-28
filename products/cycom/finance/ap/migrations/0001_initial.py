import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Vendor",
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
                ("vendor_code", models.CharField(max_length=50)),
                ("tax_id", models.CharField(blank=True, max_length=50)),
                ("payment_terms_days", models.IntegerField(default=30)),
                ("bank_account_iban", models.CharField(blank=True, max_length=34)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cycom_finance_ap_vendors"},
        ),
        migrations.CreateModel(
            name="Bill",
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
                ("bill_number", models.CharField(max_length=50)),
                ("bill_date", models.DateField()),
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
                            ("approved", "Approved"),
                            ("partial", "Partial"),
                            ("paid", "Paid"),
                            ("overdue", "Overdue"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="bills",
                        to="cycom_finance_ap.vendor",
                    ),
                ),
            ],
            options={"db_table": "cycom_finance_ap_bills"},
        ),
        migrations.CreateModel(
            name="BillLine",
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
                    "bill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="cycom_finance_ap.bill",
                    ),
                ),
            ],
            options={"db_table": "cycom_finance_ap_bill_lines"},
        ),
        migrations.CreateModel(
            name="VendorPayment",
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
                ("method", models.CharField(max_length=50)),
                ("reference", models.CharField(blank=True, max_length=100)),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payments",
                        to="cycom_finance_ap.vendor",
                    ),
                ),
                (
                    "bill",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="payments",
                        to="cycom_finance_ap.bill",
                    ),
                ),
            ],
            options={"db_table": "cycom_finance_ap_vendor_payments"},
        ),
    ]
