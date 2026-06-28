import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PurchaseOrder",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("po_number", models.CharField(max_length=50)),
                ("vendor_id", models.UUIDField(db_index=True)),
                ("po_date", models.DateField()),
                ("expected_delivery", models.DateField(blank=True, null=True)),
                ("status", models.CharField(
                    choices=[
                        ("draft", "Draft"),
                        ("approved", "Approved"),
                        ("sent", "Sent"),
                        ("partial", "Partial"),
                        ("received", "Received"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="draft",
                    max_length=20,
                )),
                ("subtotal", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("tax_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("approved_by", models.UUIDField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cycom_procurement_purchase_orders", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="POLine",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("po", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="lines",
                    to="cycom_procurement_purchase_orders.purchaseorder",
                )),
                ("item_id", models.UUIDField(db_index=True)),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=10)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=18)),
                ("tax_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("line_total", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("quantity_received", models.DecimalField(decimal_places=3, default=0, max_digits=10)),
            ],
            options={"db_table": "cycom_procurement_po_lines", "ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="GoodsReceipt",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("po", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="receipts",
                    to="cycom_procurement_purchase_orders.purchaseorder",
                )),
                ("receipt_date", models.DateField()),
                ("received_by", models.UUIDField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cycom_procurement_goods_receipts", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="GoodsReceiptLine",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("goods_receipt", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="lines",
                    to="cycom_procurement_purchase_orders.goodsreceipt",
                )),
                ("po_line", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="receipt_lines",
                    to="cycom_procurement_purchase_orders.poline",
                )),
                ("item_id", models.UUIDField()),
                ("quantity_received", models.DecimalField(decimal_places=3, max_digits=10)),
                ("batch_id", models.UUIDField(blank=True, null=True)),
                ("expiry_date", models.DateField(blank=True, null=True)),
            ],
            options={"db_table": "cycom_procurement_goods_receipt_lines", "ordering": ["created_at"]},
        ),
    ]
