import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PriceList",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("list_name", models.CharField(max_length=200)),
                ("list_code", models.CharField(max_length=50, unique=True)),
                ("facility_id", models.UUIDField(null=True, blank=True)),
                ("service_category", models.CharField(max_length=30, choices=[("hospital", "Hospital"), ("clinic", "Clinic"), ("laboratory", "Laboratory"), ("imaging", "Imaging"), ("pharmacy", "Pharmacy"), ("emergency", "Emergency"), ("package", "Package")])),
                ("currency", models.CharField(max_length=3, default="SAR")),
                ("effective_date", models.DateField()),
                ("expiry_date", models.DateField(null=True, blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_default", models.BooleanField(default=False)),
            ],
            options={"db_table": "cymed_rcm_price_lists", "ordering": ["-effective_date"]},
        ),
        migrations.CreateModel(
            name="ServicePrice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("price_list", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_prices", to="cymed_rcm_pricing.pricelist")),
                ("service_code", models.CharField(max_length=50)),
                ("service_description", models.CharField(max_length=500)),
                ("service_category", models.CharField(max_length=30)),
                ("unit_price", models.DecimalField(max_digits=12, decimal_places=2)),
                ("vat_applicable", models.BooleanField(default=True)),
                ("vat_percentage", models.DecimalField(max_digits=5, decimal_places=2, default=15)),
                ("price_includes_vat", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_rcm_price_service_prices", "ordering": ["service_code"]},
        ),
        migrations.CreateModel(
            name="PackagePrice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("price_list", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="package_prices", to="cymed_rcm_pricing.pricelist")),
                ("package_name", models.CharField(max_length=200)),
                ("package_code", models.CharField(max_length=50)),
                ("package_type", models.CharField(max_length=30, choices=[("surgical", "Surgical"), ("maternity", "Maternity"), ("oncology", "Oncology"), ("cardiac", "Cardiac"), ("orthopedic", "Orthopedic"), ("wellness", "Wellness"), ("screening", "Screening"), ("chronic_disease", "Chronic Disease"), ("other", "Other")])),
                ("package_description", models.TextField(blank=True)),
                ("package_price", models.DecimalField(max_digits=12, decimal_places=2)),
                ("services_included", models.JSONField(default=list)),
                ("valid_days", models.PositiveIntegerField(default=30)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_rcm_price_packages", "ordering": ["package_name"]},
        ),
        migrations.CreateModel(
            name="DiscountRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("rule_name", models.CharField(max_length=200)),
                ("discount_type", models.CharField(max_length=20, choices=[("percentage", "Percentage"), ("fixed_amount", "Fixed Amount"), ("waiver", "Waiver")])),
                ("applies_to", models.CharField(max_length=30, choices=[("patient_type", "Patient Type"), ("insurance", "Insurance"), ("corporate", "Corporate"), ("staff", "Staff"), ("government", "Government"), ("senior", "Senior"), ("other", "Other")])),
                ("condition_description", models.TextField(blank=True)),
                ("discount_value", models.DecimalField(max_digits=8, decimal_places=2)),
                ("max_discount_amount", models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ("requires_approval", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"db_table": "cymed_rcm_price_discount_rules", "ordering": ["rule_name"]},
        ),
    ]
