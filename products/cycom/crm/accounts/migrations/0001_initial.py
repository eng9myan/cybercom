import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CRMAccount",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account_number", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=200)),
                ("name_ar", models.CharField(blank=True, max_length=200)),
                ("account_type", models.CharField(choices=[("hospital", "Hospital"), ("clinic", "Clinic"), ("insurance", "Insurance"), ("government", "Government"), ("corporate", "Corporate")], max_length=20)),
                ("industry", models.CharField(blank=True, max_length=100)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("email", models.CharField(blank=True, max_length=254)),
                ("address", models.TextField(blank=True)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("assigned_to_id", models.UUIDField(blank=True, null=True)),
                ("annual_revenue", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("status", models.CharField(choices=[("prospect", "Prospect"), ("active", "Active"), ("inactive", "Inactive"), ("churned", "Churned")], default="prospect", max_length=20)),
            ],
            options={"db_table": "cycom_crm_accounts"},
        ),
        migrations.CreateModel(
            name="AccountContact",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contacts", to="cycom_crm_accounts.crmaccount")),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("title", models.CharField(blank=True, max_length=100)),
                ("email", models.CharField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("is_primary", models.BooleanField(default=False)),
            ],
            options={"db_table": "cycom_crm_account_contacts"},
        ),
    ]
