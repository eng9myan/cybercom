import uuid
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="VendorQualification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("vendor_id", models.UUIDField(db_index=True)),
                ("qualification_type", models.CharField(max_length=100)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("document_ref", models.CharField(blank=True, max_length=500)),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("approved", "Approved"),
                        ("rejected", "Rejected"),
                        ("expired", "Expired"),
                    ],
                    default="pending",
                    max_length=20,
                )),
            ],
            options={"db_table": "cycom_procurement_vendor_qualifications", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="VendorPerformance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("vendor_id", models.UUIDField(db_index=True)),
                ("evaluation_period", models.CharField(max_length=20)),
                ("delivery_score", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("quality_score", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("price_score", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("overall_score", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "cycom_procurement_vendor_performances", "ordering": ["-created_at"]},
        ),
    ]
