"""
Website Public API — Django Admin registrations.
Provides editorial UI for managing marketing content and reviewing leads.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ProductListing, Industry, CaseStudy,
    DemoRequest, ContactMessage,
    PartnerListing, PartnerApplication,
    DocumentationSection, DocumentationItem,
    NewsletterSubscription, WebsiteApiLog,
)


@admin.register(ProductListing)
class ProductListingAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "is_published", "is_featured", "sort_order", "updated_at"]
    list_filter = ["category", "is_published", "is_featured"]
    search_fields = ["name", "slug", "tagline"]
    list_editable = ["is_published", "is_featured", "sort_order"]
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = [
        ("Identity", {"fields": ["name", "slug", "category", "parent_product", "tagline", "short_description", "description"]}),
        ("Visual", {"fields": ["icon_class", "hero_color", "hero_image_url"]}),
        ("Content", {"fields": ["features", "key_metrics", "editions", "compliance_badges", "tech_stack", "deployment_models"]}),
        ("CTAs", {"fields": ["cta_demo_label", "cta_docs_url", "cta_video_url"]}),
        ("Publishing", {"fields": ["is_published", "is_featured", "sort_order"]}),
        ("SEO", {"fields": ["seo_title", "seo_description", "seo_keywords"]}),
    ]


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_published", "is_featured", "sort_order"]
    list_filter = ["is_published", "is_featured"]
    search_fields = ["name", "slug"]
    list_editable = ["is_published", "is_featured", "sort_order"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["relevant_products"]


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ["title", "customer_name", "country", "industry", "is_published", "is_featured", "published_at"]
    list_filter = ["is_published", "is_featured", "industry", "country"]
    search_fields = ["title", "customer_name", "summary"]
    list_editable = ["is_published", "is_featured"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["products"]


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number", "full_name", "company", "email",
        "status", "product_interests_display", "country", "created_at",
    ]
    list_filter = ["status", "country", "company_size"]
    search_fields = ["reference_number", "full_name", "email", "company"]
    readonly_fields = [
        "id", "reference_number", "ip_address", "user_agent",
        "utm_source", "utm_medium", "utm_campaign",
        "referrer_url", "landing_page", "created_at",
    ]
    list_editable = ["status"]

    def product_interests_display(self, obj):
        return ", ".join(obj.product_interests[:3]) if obj.product_interests else "—"
    product_interests_display.short_description = "Products"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["ticket_number", "full_name", "email", "department", "subject_short", "status", "created_at"]
    list_filter = ["status", "department"]
    search_fields = ["ticket_number", "full_name", "email", "subject"]
    readonly_fields = ["id", "ticket_number", "ip_address", "user_agent", "created_at"]
    list_editable = ["status"]

    def subject_short(self, obj):
        return obj.subject[:50]
    subject_short.short_description = "Subject"


@admin.register(PartnerListing)
class PartnerListingAdmin(admin.ModelAdmin):
    list_display = ["company_name", "partner_type", "is_published", "is_featured", "sort_order"]
    list_filter = ["partner_type", "is_published", "is_featured"]
    search_fields = ["company_name", "slug"]
    list_editable = ["is_published", "is_featured", "sort_order"]
    prepopulated_fields = {"slug": ("company_name",)}


@admin.register(PartnerApplication)
class PartnerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number", "company_name", "contact_name",
        "email", "partner_type", "status", "created_at",
    ]
    list_filter = ["status", "partner_type"]
    search_fields = ["reference_number", "company_name", "email"]
    readonly_fields = ["id", "reference_number", "ip_address", "user_agent", "created_at"]
    list_editable = ["status"]


class DocumentationItemInline(admin.TabularInline):
    model = DocumentationItem
    extra = 0
    fields = ["title", "slug", "content_type", "sort_order", "is_published"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(DocumentationSection)
class DocumentationSectionAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "product", "sort_order", "is_published"]
    list_filter = ["is_published", "product"]
    search_fields = ["title", "slug"]
    list_editable = ["sort_order", "is_published"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [DocumentationItemInline]


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["email", "status", "source", "created_at"]
    list_filter = ["status", "source"]
    search_fields = ["email"]
    readonly_fields = ["created_at", "ip_address"]


@admin.register(WebsiteApiLog)
class WebsiteApiLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "method", "endpoint", "status_code", "response_time_ms", "ip_address", "was_throttled"]
    list_filter = ["status_code", "method", "was_throttled"]
    search_fields = ["endpoint", "ip_address"]
    readonly_fields = [f.name for f in WebsiteApiLog._meta.get_fields()]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
