"""
Initial migration for products.website — public website integration APIs.
"""

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProductListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("tagline", models.CharField(blank=True, max_length=300)),
                ("short_description", models.TextField(blank=True)),
                ("description", models.TextField(blank=True)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("healthcare", "Healthcare"),
                            ("erp", "ERP & Business"),
                            ("government", "Government"),
                            ("ai", "AI Platform"),
                            ("identity", "Identity & Security"),
                            ("integration", "Integration"),
                            ("data", "Data Platform"),
                            ("communications", "Communications"),
                            ("citizen", "Citizen Services"),
                        ],
                        db_index=True,
                        max_length=30,
                    ),
                ),
                (
                    "parent_product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sub_products",
                        to="website.productlisting",
                    ),
                ),
                ("icon_class", models.CharField(blank=True, max_length=100)),
                ("hero_color", models.CharField(blank=True, max_length=20)),
                ("hero_image_url", models.URLField(blank=True)),
                ("features", models.JSONField(blank=True, default=list)),
                ("key_metrics", models.JSONField(blank=True, default=list)),
                ("editions", models.JSONField(blank=True, default=list)),
                ("compliance_badges", models.JSONField(blank=True, default=list)),
                ("tech_stack", models.JSONField(blank=True, default=list)),
                ("deployment_models", models.JSONField(blank=True, default=list)),
                ("cta_demo_label", models.CharField(default="Request Demo", max_length=100)),
                ("cta_docs_url", models.URLField(blank=True)),
                ("cta_video_url", models.URLField(blank=True)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("sort_order", models.PositiveSmallIntegerField(db_index=True, default=0)),
                ("seo_title", models.CharField(blank=True, max_length=200)),
                ("seo_description", models.CharField(blank=True, max_length=500)),
                ("seo_keywords", models.JSONField(default=list)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "website_product_listings", "ordering": ["sort_order", "name"]},
        ),
        migrations.CreateModel(
            name="Industry",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=150)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("description", models.TextField(blank=True)),
                ("short_description", models.CharField(blank=True, max_length=300)),
                ("icon_class", models.CharField(blank=True, max_length=100)),
                ("hero_image_url", models.URLField(blank=True)),
                ("challenges", models.JSONField(blank=True, default=list)),
                ("solutions", models.JSONField(blank=True, default=list)),
                (
                    "relevant_products",
                    models.ManyToManyField(
                        blank=True, related_name="industries", to="website.productlisting"
                    ),
                ),
                ("stats", models.JSONField(blank=True, default=list)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("seo_title", models.CharField(blank=True, max_length=200)),
                ("seo_description", models.CharField(blank=True, max_length=500)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "website_industries",
                "ordering": ["sort_order", "name"],
                "verbose_name_plural": "industries",
            },
        ),
        migrations.CreateModel(
            name="CaseStudy",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("title", models.CharField(max_length=300)),
                ("slug", models.SlugField(max_length=180, unique=True)),
                ("customer_name", models.CharField(max_length=200)),
                ("customer_logo_url", models.URLField(blank=True)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("region", models.CharField(blank=True, max_length=100)),
                (
                    "industry",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="case_studies",
                        to="website.industry",
                    ),
                ),
                (
                    "products",
                    models.ManyToManyField(
                        blank=True, related_name="case_studies", to="website.productlisting"
                    ),
                ),
                ("summary", models.TextField(blank=True)),
                ("challenge", models.TextField(blank=True)),
                ("solution", models.TextField(blank=True)),
                ("outcome", models.TextField(blank=True)),
                ("metrics", models.JSONField(blank=True, default=list)),
                ("quote", models.TextField(blank=True)),
                ("quote_author", models.CharField(blank=True, max_length=200)),
                ("quote_title", models.CharField(blank=True, max_length=200)),
                ("hero_image_url", models.URLField(blank=True)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("seo_title", models.CharField(blank=True, max_length=200)),
                ("seo_description", models.CharField(blank=True, max_length=500)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "website_case_studies",
                "ordering": ["-published_at", "-created_at"],
                "verbose_name_plural": "case studies",
            },
        ),
        migrations.CreateModel(
            name="DemoRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("reference_number", models.CharField(editable=False, max_length=20, unique=True)),
                ("full_name", models.CharField(max_length=200)),
                ("email", models.EmailField(db_index=True)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("job_title", models.CharField(blank=True, max_length=200)),
                ("company", models.CharField(blank=True, max_length=200)),
                ("company_size", models.CharField(blank=True, max_length=50)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("product_interests", models.JSONField(default=list)),
                ("message", models.TextField(blank=True)),
                ("preferred_time", models.CharField(blank=True, max_length=200)),
                ("preferred_date", models.DateField(blank=True, null=True)),
                ("source", models.CharField(blank=True, max_length=100)),
                ("utm_source", models.CharField(blank=True, max_length=100)),
                ("utm_medium", models.CharField(blank=True, max_length=100)),
                ("utm_campaign", models.CharField(blank=True, max_length=100)),
                ("referrer_url", models.URLField(blank=True)),
                ("landing_page", models.URLField(blank=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("tenant_slug", models.CharField(blank=True, db_index=True, max_length=100)),
                ("crm_lead_id", models.CharField(blank=True, max_length=200)),
                ("crm_synced_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("contacted", "Contacted"),
                            ("scheduled", "Scheduled"),
                            ("completed", "Demo Completed"),
                            ("closed", "Closed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("assigned_to", models.CharField(blank=True, max_length=200)),
                ("notes", models.TextField(blank=True)),
                ("gdpr_consent", models.BooleanField(default=False)),
                ("marketing_consent", models.BooleanField(default=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "website_demo_requests", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("ticket_number", models.CharField(editable=False, max_length=20, unique=True)),
                ("full_name", models.CharField(max_length=200)),
                ("email", models.EmailField(db_index=True)),
                ("company", models.CharField(blank=True, max_length=200)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("subject", models.CharField(max_length=300)),
                ("message", models.TextField()),
                (
                    "department",
                    models.CharField(
                        choices=[
                            ("sales", "Sales"),
                            ("support", "Support"),
                            ("partnerships", "Partnerships"),
                            ("press", "Press & Media"),
                            ("careers", "Careers"),
                            ("general", "General"),
                        ],
                        db_index=True,
                        default="general",
                        max_length=30,
                    ),
                ),
                ("source", models.CharField(blank=True, max_length=100)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("in_progress", "In Progress"),
                            ("resolved", "Resolved"),
                            ("closed", "Closed"),
                        ],
                        db_index=True,
                        default="new",
                        max_length=20,
                    ),
                ),
                ("assigned_to", models.CharField(blank=True, max_length=200)),
                ("response_notes", models.TextField(blank=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("gdpr_consent", models.BooleanField(default=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "website_contact_messages", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PartnerListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("company_name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("logo_url", models.URLField(blank=True)),
                ("website", models.URLField(blank=True)),
                ("description", models.TextField(blank=True)),
                (
                    "partner_type",
                    models.CharField(
                        choices=[
                            ("reseller", "Reseller"),
                            ("implementation", "Implementation Partner"),
                            ("technology", "Technology Partner"),
                            ("isv", "ISV / Software Partner"),
                            ("referral", "Referral Partner"),
                            ("strategic", "Strategic Alliance"),
                        ],
                        db_index=True,
                        max_length=30,
                    ),
                ),
                ("expertise_areas", models.JSONField(blank=True, default=list)),
                ("countries", models.JSONField(blank=True, default=list)),
                ("languages", models.JSONField(blank=True, default=list)),
                ("certifications", models.JSONField(blank=True, default=list)),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "website_partner_listings",
                "ordering": ["sort_order", "company_name"],
            },
        ),
        migrations.CreateModel(
            name="PartnerApplication",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("reference_number", models.CharField(editable=False, max_length=20, unique=True)),
                ("company_name", models.CharField(max_length=200)),
                ("contact_name", models.CharField(max_length=200)),
                ("email", models.EmailField(db_index=True)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("website", models.URLField(blank=True)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("partner_type", models.CharField(max_length=30)),
                ("expertise_areas", models.JSONField(blank=True, default=list)),
                ("years_in_business", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("employee_count", models.CharField(blank=True, max_length=50)),
                ("message", models.TextField(blank=True)),
                ("existing_customers", models.TextField(blank=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("status", models.CharField(db_index=True, default="pending", max_length=20)),
                ("reviewed_by", models.CharField(blank=True, max_length=200)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_notes", models.TextField(blank=True)),
                ("gdpr_consent", models.BooleanField(default=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "website_partner_applications", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DocumentationSection",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doc_sections",
                        to="website.productlisting",
                    ),
                ),
                ("icon_class", models.CharField(blank=True, max_length=100)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "website_doc_sections", "ordering": ["sort_order", "title"]},
        ),
        migrations.CreateModel(
            name="DocumentationItem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="website.documentationsection",
                    ),
                ),
                ("title", models.CharField(max_length=300)),
                ("slug", models.SlugField(max_length=200)),
                (
                    "content_type",
                    models.CharField(
                        choices=[
                            ("guide", "Guide"),
                            ("reference", "API Reference"),
                            ("tutorial", "Tutorial"),
                            ("release_note", "Release Note"),
                            ("faq", "FAQ"),
                            ("changelog", "Changelog"),
                        ],
                        db_index=True,
                        max_length=30,
                    ),
                ),
                ("summary", models.TextField(blank=True)),
                ("content_url", models.URLField(blank=True)),
                ("external_url", models.URLField(blank=True)),
                ("version", models.CharField(blank=True, max_length=30)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "website_doc_items",
                "ordering": ["sort_order", "title"],
                "unique_together": {("section", "slug")},
            },
        ),
        migrations.CreateModel(
            name="NewsletterSubscription",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("email", models.EmailField(db_index=True, unique=True)),
                ("source", models.CharField(blank=True, max_length=100)),
                ("status", models.CharField(db_index=True, default="pending", max_length=20)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("unsubscribed_at", models.DateTimeField(blank=True, null=True)),
                ("gdpr_consent", models.BooleanField(default=False)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "website_newsletter_subscriptions", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="WebsiteApiLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("endpoint", models.CharField(db_index=True, max_length=200)),
                ("method", models.CharField(max_length=10)),
                ("status_code", models.PositiveSmallIntegerField(db_index=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("referrer", models.URLField(blank=True)),
                ("response_time_ms", models.PositiveIntegerField(default=0)),
                ("resource_type", models.CharField(blank=True, max_length=50)),
                ("resource_id", models.CharField(blank=True, max_length=100)),
                ("was_throttled", models.BooleanField(default=False)),
                ("error_detail", models.TextField(blank=True)),
            ],
            options={"db_table": "website_api_logs", "ordering": ["-timestamp"]},
        ),
        migrations.AddIndex(
            model_name="productlisting",
            index=models.Index(fields=["category", "is_published"], name="website_pl_cat_pub_idx"),
        ),
        migrations.AddIndex(
            model_name="productlisting",
            index=models.Index(
                fields=["is_featured", "is_published"], name="website_pl_feat_pub_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="demorequest",
            index=models.Index(fields=["status", "created_at"], name="website_dr_status_idx"),
        ),
        migrations.AddIndex(
            model_name="demorequest",
            index=models.Index(fields=["email", "created_at"], name="website_dr_email_idx"),
        ),
        migrations.AddIndex(
            model_name="websiteapilog",
            index=models.Index(fields=["endpoint", "timestamp"], name="website_log_ep_ts_idx"),
        ),
        migrations.AddIndex(
            model_name="websiteapilog",
            index=models.Index(fields=["status_code", "timestamp"], name="website_log_sc_ts_idx"),
        ),
    ]
