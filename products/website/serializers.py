"""
Website Public API — Serializers.
Read serializers for content; write serializers for lead capture with validation.
"""
import re
from django.utils import timezone
from rest_framework import serializers

from .models import (
    ProductListing, Industry, CaseStudy,
    DemoRequest, ContactMessage, PartnerListing, PartnerApplication,
    DocumentationSection, DocumentationItem, NewsletterSubscription,
)


# ---------------------------------------------------------------------------
# Content — Read Serializers
# ---------------------------------------------------------------------------

class ProductListingListSerializer(serializers.ModelSerializer):
    """Compact product listing for index pages."""
    class Meta:
        model = ProductListing
        fields = [
            "id", "name", "slug", "tagline", "short_description",
            "category", "icon_class", "hero_color", "hero_image_url",
            "is_featured", "sort_order", "seo_title", "seo_description",
        ]


class ProductListingDetailSerializer(serializers.ModelSerializer):
    """Full product detail including features, editions, compliance."""
    sub_products = ProductListingListSerializer(many=True, read_only=True)

    class Meta:
        model = ProductListing
        fields = [
            "id", "name", "slug", "tagline", "short_description", "description",
            "category", "icon_class", "hero_color", "hero_image_url",
            "features", "key_metrics", "editions", "compliance_badges",
            "tech_stack", "deployment_models",
            "cta_demo_label", "cta_docs_url", "cta_video_url",
            "is_featured", "sort_order",
            "seo_title", "seo_description", "seo_keywords",
            "sub_products", "updated_at",
        ]


class IndustryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = [
            "id", "name", "slug", "short_description",
            "icon_class", "hero_image_url", "is_featured", "sort_order",
            "seo_title", "seo_description",
        ]


class IndustryDetailSerializer(serializers.ModelSerializer):
    relevant_products = ProductListingListSerializer(many=True, read_only=True)

    class Meta:
        model = Industry
        fields = [
            "id", "name", "slug", "description", "short_description",
            "icon_class", "hero_image_url",
            "challenges", "solutions", "stats",
            "relevant_products",
            "is_featured", "sort_order",
            "seo_title", "seo_description", "updated_at",
        ]


class CaseStudyListSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source="industry.name", read_only=True, default=None)

    class Meta:
        model = CaseStudy
        fields = [
            "id", "title", "slug", "customer_name", "customer_logo_url",
            "country", "region", "industry_name",
            "summary", "metrics", "quote", "quote_author",
            "hero_image_url", "is_featured", "published_at",
            "seo_title", "seo_description",
        ]


class CaseStudyDetailSerializer(serializers.ModelSerializer):
    industry = IndustryListSerializer(read_only=True)
    products = ProductListingListSerializer(many=True, read_only=True)

    class Meta:
        model = CaseStudy
        fields = [
            "id", "title", "slug", "customer_name", "customer_logo_url",
            "country", "region", "industry", "products",
            "summary", "challenge", "solution", "outcome",
            "metrics", "quote", "quote_author", "quote_title",
            "hero_image_url", "is_featured", "published_at",
            "seo_title", "seo_description", "updated_at",
        ]


class PartnerListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerListing
        fields = [
            "id", "company_name", "slug", "logo_url", "website",
            "description", "partner_type", "expertise_areas",
            "countries", "languages", "certifications",
            "is_featured", "sort_order",
        ]


class DocumentationSectionSerializer(serializers.ModelSerializer):
    product_slug = serializers.CharField(source="product.slug", read_only=True, default=None)

    class Meta:
        model = DocumentationSection
        fields = [
            "id", "title", "slug", "description",
            "product_slug", "icon_class", "sort_order",
        ]


class DocumentationItemSerializer(serializers.ModelSerializer):
    section_slug = serializers.CharField(source="section.slug", read_only=True)

    class Meta:
        model = DocumentationItem
        fields = [
            "id", "title", "slug", "section_slug", "content_type",
            "summary", "content_url", "external_url",
            "version", "tags", "sort_order", "published_at",
        ]


class DocumentationSectionDetailSerializer(serializers.ModelSerializer):
    product_slug = serializers.CharField(source="product.slug", read_only=True, default=None)
    items = DocumentationItemSerializer(many=True, read_only=True)

    class Meta:
        model = DocumentationSection
        fields = [
            "id", "title", "slug", "description",
            "product_slug", "icon_class", "sort_order", "items",
        ]


# ---------------------------------------------------------------------------
# Lead Capture — Write Serializers
# ---------------------------------------------------------------------------

DISPOSABLE_DOMAINS = frozenset([
    "mailinator.com", "guerrillamail.com", "tempmail.com",
    "throwaway.email", "yopmail.com", "sharklasers.com",
])


def _validate_business_email(email: str) -> str:
    domain = email.split("@")[-1].lower()
    if domain in DISPOSABLE_DOMAINS:
        raise serializers.ValidationError("Please use a business email address.")
    return email


class DemoRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoRequest
        fields = [
            "full_name", "email", "phone", "job_title",
            "company", "company_size", "country",
            "product_interests", "message",
            "preferred_time", "preferred_date",
            "source", "utm_source", "utm_medium", "utm_campaign",
            "referrer_url", "landing_page",
            "gdpr_consent", "marketing_consent",
        ]

    def validate_email(self, value: str) -> str:
        return _validate_business_email(value.lower().strip())

    def validate_full_name(self, value: str) -> str:
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Please provide your full name.")
        return value.strip()

    def validate_product_interests(self, value) -> list:
        if not value:
            raise serializers.ValidationError("Please select at least one product of interest.")
        return value

    def validate_gdpr_consent(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Consent to data processing is required.")
        return value


class DemoRequestResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoRequest
        fields = ["id", "reference_number", "status", "created_at"]


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = [
            "full_name", "email", "company", "phone",
            "subject", "message", "department",
            "source", "gdpr_consent",
        ]

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_message(self, value: str) -> str:
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters.")
        return value.strip()

    def validate_gdpr_consent(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Consent to data processing is required.")
        return value


class ContactMessageResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "ticket_number", "status", "created_at"]


class PartnerApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerApplication
        fields = [
            "company_name", "contact_name", "email", "phone",
            "website", "country", "partner_type",
            "expertise_areas", "years_in_business", "employee_count",
            "message", "existing_customers", "gdpr_consent",
        ]

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_gdpr_consent(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Consent to data processing is required.")
        return value


class PartnerApplicationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerApplication
        fields = ["id", "reference_number", "status", "created_at"]


class NewsletterSubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    source = serializers.CharField(max_length=100, required=False, default="")
    gdpr_consent = serializers.BooleanField()

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_gdpr_consent(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Consent to data processing is required.")
        return value
