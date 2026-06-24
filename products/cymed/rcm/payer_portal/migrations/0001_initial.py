import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PayerPortalAccount",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("insurance_company_id", models.UUIDField(db_index=True)),
                ("cyidentity_user_id", models.UUIDField(db_index=True)),
                ("account_role", models.CharField(max_length=30, choices=[("claims_reviewer", "Claims Reviewer"), ("eligibility_reviewer", "Eligibility Reviewer"), ("auth_reviewer", "Authorization Reviewer"), ("appeals_reviewer", "Appeals Reviewer"), ("account_manager", "Account Manager"), ("admin", "Admin")])),
                ("is_active", models.BooleanField(default=True)),
                ("access_level", models.CharField(max_length=20, default="reviewer", choices=[("read_only", "Read Only"), ("reviewer", "Reviewer"), ("approver", "Approver"), ("admin", "Admin")])),
                ("last_login", models.DateTimeField(null=True, blank=True)),
            ],
            options={"db_table": "cymed_rcm_payer_accounts", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PayerDashboard",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("payer_account", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="dashboard", to="cymed_rcm_payer_portal.payerportalaccount")),
                ("pending_claims_count", models.PositiveIntegerField(default=0)),
                ("pending_auths_count", models.PositiveIntegerField(default=0)),
                ("pending_appeals_count", models.PositiveIntegerField(default=0)),
                ("last_refreshed_at", models.DateTimeField(null=True, blank=True)),
                ("dashboard_config", models.JSONField(default=dict)),
            ],
            options={"db_table": "cymed_rcm_payer_dashboards"},
        ),
        migrations.CreateModel(
            name="PayerClaimReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("payer_account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="claim_reviews", to="cymed_rcm_payer_portal.payerportalaccount")),
                ("claim_id", models.UUIDField(db_index=True)),
                ("review_status", models.CharField(max_length=30, default="pending", choices=[("pending", "Pending"), ("under_review", "Under Review"), ("additional_info_requested", "Additional Info Requested"), ("decision_made", "Decision Made")])),
                ("reviewer_notes", models.TextField(blank=True)),
                ("decision", models.CharField(max_length=20, blank=True)),
                ("decision_date", models.DateTimeField(null=True, blank=True)),
                ("additional_info_requested", models.TextField(blank=True)),
                ("info_due_date", models.DateField(null=True, blank=True)),
            ],
            options={"db_table": "cymed_rcm_payer_claim_reviews", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PayerAuthorizationReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("payer_account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="auth_reviews", to="cymed_rcm_payer_portal.payerportalaccount")),
                ("preauthorization_id", models.UUIDField(db_index=True)),
                ("review_status", models.CharField(max_length=30, default="pending", choices=[("pending", "Pending"), ("under_review", "Under Review"), ("clinical_review", "Clinical Review"), ("decision_made", "Decision Made")])),
                ("reviewer_notes", models.TextField(blank=True)),
                ("decision", models.CharField(max_length=20, blank=True)),
                ("approved_units", models.PositiveIntegerField(null=True, blank=True)),
                ("approved_start_date", models.DateField(null=True, blank=True)),
                ("approved_end_date", models.DateField(null=True, blank=True)),
                ("decision_date", models.DateTimeField(null=True, blank=True)),
            ],
            options={"db_table": "cymed_rcm_payer_auth_reviews", "ordering": ["-created_at"]},
        ),
    ]
