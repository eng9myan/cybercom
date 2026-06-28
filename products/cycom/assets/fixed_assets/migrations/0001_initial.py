import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AssetCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("code", models.CharField(max_length=20)),
                ("name", models.CharField(max_length=200)),
                ("useful_life_years", models.IntegerField(default=5)),
                ("depreciation_method", models.CharField(
                    choices=[
                        ("straight_line", "Straight Line"),
                        ("declining_balance", "Declining Balance"),
                    ],
                    default="straight_line",
                    max_length=20,
                )),
                ("salvage_pct", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
            ],
            options={"db_table": "cycom_assets_fixed_asset_categories", "ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="FixedAsset",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("asset_number", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=200)),
                ("name_ar", models.CharField(blank=True, max_length=200)),
                ("category", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="assets",
                    to="cycom_assets_fixed_assets.assetcategory",
                )),
                ("acquisition_date", models.DateField()),
                ("acquisition_cost", models.DecimalField(decimal_places=2, max_digits=18)),
                ("current_book_value", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("depreciation_accumulated", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("status", models.CharField(
                    choices=[
                        ("active", "Active"),
                        ("disposed", "Disposed"),
                        ("under_maintenance", "Under Maintenance"),
                        ("written_off", "Written Off"),
                    ],
                    default="active",
                    max_length=20,
                )),
                ("location", models.CharField(blank=True, max_length=200)),
                ("assigned_to", models.UUIDField(blank=True, null=True)),
            ],
            options={"db_table": "cycom_assets_fixed_assets", "ordering": ["asset_number"]},
        ),
        migrations.CreateModel(
            name="Depreciation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("asset", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="depreciations",
                    to="cycom_assets_fixed_assets.fixedasset",
                )),
                ("period_year", models.IntegerField()),
                ("period_month", models.IntegerField()),
                ("depreciation_amount", models.DecimalField(decimal_places=2, max_digits=18)),
                ("book_value_after", models.DecimalField(decimal_places=2, max_digits=18)),
                ("posted", models.BooleanField(default=False)),
            ],
            options={"db_table": "cycom_assets_depreciations", "ordering": ["period_year", "period_month"]},
        ),
    ]
