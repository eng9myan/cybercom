"""
Website Public API — Tests.
Covers all 7 endpoint groups: products, industries, case-studies, partners,
documentation, demo-request, contact.
"""
import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from products.website.models import (
    ProductListing, Industry, CaseStudy,
    DemoRequest, ContactMessage,
    PartnerListing, PartnerApplication,
    DocumentationSection, DocumentationItem,
    NewsletterSubscription,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_product(**kwargs):
    defaults = {
        "name": "CyMed Hospital",
        "slug": f"cymed-hospital-{uuid.uuid4().hex[:6]}",
        "tagline": "Enterprise Hospital Management",
        "category": "healthcare",
        "is_published": True,
        "is_featured": True,
        "sort_order": 1,
    }
    defaults.update(kwargs)
    return ProductListing.objects.create(**defaults)


def make_industry(**kwargs):
    defaults = {
        "name": "Healthcare",
        "slug": f"healthcare-{uuid.uuid4().hex[:6]}",
        "short_description": "Hospitals, clinics, and health systems.",
        "is_published": True,
        "is_featured": True,
    }
    defaults.update(kwargs)
    return Industry.objects.create(**defaults)


def make_case_study(industry=None, **kwargs):
    defaults = {
        "title": "King Faisal Medical City Deploys CyMed",
        "slug": f"kfmc-cymed-{uuid.uuid4().hex[:6]}",
        "customer_name": "King Faisal Medical City",
        "country": "Saudi Arabia",
        "industry": industry,
        "is_published": True,
        "is_featured": True,
    }
    defaults.update(kwargs)
    return CaseStudy.objects.create(**defaults)


def make_partner(**kwargs):
    defaults = {
        "company_name": "AlSharq Consulting",
        "slug": f"alsharq-{uuid.uuid4().hex[:6]}",
        "partner_type": "implementation",
        "is_published": True,
    }
    defaults.update(kwargs)
    return PartnerListing.objects.create(**defaults)


def make_doc_section(product=None, **kwargs):
    defaults = {
        "title": "Getting Started with CyMed",
        "slug": f"getting-started-{uuid.uuid4().hex[:6]}",
        "product": product,
        "is_published": True,
    }
    defaults.update(kwargs)
    return DocumentationSection.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class WebsiteApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def url(self, name, **kwargs):
        return reverse(f"website:{name}", kwargs=kwargs)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class PublicHealthTests(WebsiteApiTestCase):
    def test_health_returns_ok(self):
        resp = self.client.get("/api/v1/public/health/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "ok")
        self.assertIn("endpoints", resp.data)

    def test_health_no_auth_required(self):
        resp = self.client.get("/api/v1/public/health/")
        self.assertNotEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class ProductListTests(WebsiteApiTestCase):
    def setUp(self):
        super().setUp()
        self.p1 = make_product(name="CyMed Hospital", category="healthcare", is_featured=True)
        self.p2 = make_product(name="CyCom Finance", category="erp", is_featured=False)
        # unpublished — should never appear
        make_product(name="Draft Product", is_published=False)

    def test_list_returns_published_only(self):
        resp = self.client.get("/api/v1/public/products/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = [r["slug"] for r in resp.data["results"]]
        self.assertIn(self.p1.slug, slugs)
        self.assertIn(self.p2.slug, slugs)
        self.assertFalse(any("Draft" in r["name"] for r in resp.data["results"]))

    def test_filter_by_category(self):
        resp = self.client.get("/api/v1/public/products/?category=healthcare")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for r in resp.data["results"]:
            self.assertEqual(r["category"], "healthcare")

    def test_filter_featured(self):
        resp = self.client.get("/api/v1/public/products/?is_featured=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for r in resp.data["results"]:
            self.assertTrue(r["is_featured"])

    def test_search(self):
        resp = self.client.get("/api/v1/public/products/?search=Hospital")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(any("Hospital" in r["name"] for r in resp.data["results"]))

    def test_detail_returns_full_object(self):
        resp = self.client.get(f"/api/v1/public/products/{self.p1.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["slug"], self.p1.slug)
        self.assertIn("features", resp.data)
        self.assertIn("editions", resp.data)

    def test_detail_unpublished_returns_404(self):
        unpub = make_product(is_published=False)
        resp = self.client.get(f"/api/v1/public/products/{unpub.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Industries
# ---------------------------------------------------------------------------

class IndustryTests(WebsiteApiTestCase):
    def setUp(self):
        super().setUp()
        self.i1 = make_industry(name="Healthcare", is_featured=True)
        make_industry(name="Government", is_published=False)

    def test_list_published_only(self):
        resp = self.client.get("/api/v1/public/industries/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [r["name"] for r in resp.data["results"]]
        self.assertIn("Healthcare", names)
        self.assertNotIn("Government", names)

    def test_featured_filter(self):
        resp = self.client.get("/api/v1/public/industries/?is_featured=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(all(r["is_featured"] for r in resp.data["results"]))

    def test_detail(self):
        resp = self.client.get(f"/api/v1/public/industries/{self.i1.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("challenges", resp.data)
        self.assertIn("relevant_products", resp.data)


# ---------------------------------------------------------------------------
# Case Studies
# ---------------------------------------------------------------------------

class CaseStudyTests(WebsiteApiTestCase):
    def setUp(self):
        super().setUp()
        self.industry = make_industry()
        self.cs = make_case_study(industry=self.industry)
        make_case_study(is_published=False)

    def test_list_published_only(self):
        resp = self.client.get("/api/v1/public/case-studies/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_industry(self):
        resp = self.client.get(f"/api/v1/public/case-studies/?industry={self.industry.slug}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["slug"], self.cs.slug)

    def test_detail(self):
        resp = self.client.get(f"/api/v1/public/case-studies/{self.cs.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("challenge", resp.data)
        self.assertIn("outcome", resp.data)
        self.assertIn("metrics", resp.data)


# ---------------------------------------------------------------------------
# Partners
# ---------------------------------------------------------------------------

class PartnerTests(WebsiteApiTestCase):
    def setUp(self):
        super().setUp()
        self.p = make_partner()
        make_partner(is_published=False)

    def test_list_published(self):
        resp = self.client.get("/api/v1/public/partners/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_type(self):
        resp = self.client.get("/api/v1/public/partners/?partner_type=implementation")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_apply_valid(self):
        payload = {
            "company_name": "Nile Tech",
            "contact_name": "Ahmed Hassan",
            "email": "ahmed@niletech.eg",
            "partner_type": "reseller",
            "country": "Egypt",
            "gdpr_consent": True,
        }
        resp = self.client.post("/api/v1/public/partners/apply/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("reference_number", resp.data)
        self.assertTrue(resp.data["reference_number"].startswith("PAR-"))

    def test_apply_missing_gdpr(self):
        payload = {
            "company_name": "Nile Tech",
            "contact_name": "Ahmed",
            "email": "ahmed@niletech.eg",
            "partner_type": "reseller",
            "gdpr_consent": False,
        }
        resp = self.client.post("/api/v1/public/partners/apply/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gdpr_consent", resp.data["errors"])


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

class DocumentationTests(WebsiteApiTestCase):
    def setUp(self):
        super().setUp()
        self.product = make_product()
        self.section = make_doc_section(product=self.product)
        self.item = DocumentationItem.objects.create(
            section=self.section,
            title="Quick Start Guide",
            slug="quick-start",
            content_type="guide",
            summary="Get started with CyMed in 5 minutes.",
            is_published=True,
            tags=["setup", "quickstart"],
        )

    def test_section_list(self):
        resp = self.client.get("/api/v1/public/documentation/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_section_filter_by_product(self):
        resp = self.client.get(f"/api/v1/public/documentation/?product={self.product.slug}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_section_detail_includes_items(self):
        resp = self.client.get(f"/api/v1/public/documentation/{self.section.slug}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("items", resp.data)
        self.assertEqual(len(resp.data["items"]), 1)
        self.assertEqual(resp.data["items"][0]["slug"], "quick-start")

    def test_search_by_title(self):
        resp = self.client.get("/api/v1/public/documentation/search/?q=Quick")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_search_too_short(self):
        resp = self.client.get("/api/v1/public/documentation/search/?q=Q")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_tag(self):
        resp = self.client.get("/api/v1/public/documentation/search/?q=quickstart")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["count"], 1)


# ---------------------------------------------------------------------------
# Demo Request
# ---------------------------------------------------------------------------

class DemoRequestTests(WebsiteApiTestCase):
    VALID_PAYLOAD = {
        "full_name": "Sara Al-Nour",
        "email": "sara@hospital.sa",
        "company": "King Faisal Medical City",
        "job_title": "CIO",
        "product_interests": ["CyMed Hospital", "CyMed Pharmacy"],
        "country": "Saudi Arabia",
        "gdpr_consent": True,
    }

    def test_create_valid(self):
        resp = self.client.post("/api/v1/public/demo-request/", self.VALID_PAYLOAD, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("reference_number", resp.data)
        self.assertTrue(resp.data["reference_number"].startswith("CYB-"))
        self.assertEqual(resp.data["status"], "pending")

    def test_create_without_gdpr_fails(self):
        payload = {**self.VALID_PAYLOAD, "gdpr_consent": False}
        resp = self.client.post("/api/v1/public/demo-request/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gdpr_consent", resp.data["errors"])

    def test_create_without_product_interests_fails(self):
        payload = {**self.VALID_PAYLOAD, "product_interests": []}
        resp = self.client.post("/api/v1/public/demo-request/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_disposable_email_fails(self):
        payload = {**self.VALID_PAYLOAD, "email": "test@mailinator.com"}
        resp = self.client.post("/api/v1/public/demo-request/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_endpoint(self):
        create_resp = self.client.post("/api/v1/public/demo-request/", self.VALID_PAYLOAD, format="json")
        ref = create_resp.data["reference_number"]
        resp = self.client.get(f"/api/v1/public/demo-request/{ref}/status/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["reference_number"], ref)

    def test_status_not_found(self):
        resp = self.client.get("/api/v1/public/demo-request/CYB-999999/status/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_saves_to_db(self):
        self.client.post("/api/v1/public/demo-request/", self.VALID_PAYLOAD, format="json")
        self.assertEqual(DemoRequest.objects.count(), 1)
        dr = DemoRequest.objects.first()
        self.assertEqual(dr.email, "sara@hospital.sa")
        self.assertEqual(dr.status, "pending")


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class ContactTests(WebsiteApiTestCase):
    VALID_PAYLOAD = {
        "full_name": "Mohammed Al-Rashid",
        "email": "mohammed@company.com",
        "subject": "Enterprise Pricing Inquiry",
        "message": "We are interested in evaluating CyMed for our hospital network of 12 facilities.",
        "department": "sales",
        "gdpr_consent": True,
    }

    def test_create_valid(self):
        resp = self.client.post("/api/v1/public/contact/", self.VALID_PAYLOAD, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("ticket_number", resp.data)
        self.assertTrue(resp.data["ticket_number"].startswith("TKT-"))

    def test_message_too_short(self):
        payload = {**self.VALID_PAYLOAD, "message": "Hi"}
        resp = self.client.post("/api/v1/public/contact/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_endpoint(self):
        create_resp = self.client.post("/api/v1/public/contact/", self.VALID_PAYLOAD, format="json")
        ticket = create_resp.data["ticket_number"]
        resp = self.client.get(f"/api/v1/public/contact/{ticket}/status/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_saves_to_db(self):
        self.client.post("/api/v1/public/contact/", self.VALID_PAYLOAD, format="json")
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.department, "sales")


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class NewsletterTests(WebsiteApiTestCase):
    def test_subscribe_valid(self):
        payload = {"email": "user@company.com", "gdpr_consent": True, "source": "footer"}
        resp = self.client.post("/api/v1/public/contact/newsletter/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("status", resp.data)

    def test_duplicate_subscribe_returns_200(self):
        payload = {"email": "dup@company.com", "gdpr_consent": True}
        self.client.post("/api/v1/public/contact/newsletter/", payload, format="json")
        resp = self.client.post("/api/v1/public/contact/newsletter/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_without_gdpr_fails(self):
        payload = {"email": "user@company.com", "gdpr_consent": False}
        resp = self.client.post("/api/v1/public/contact/newsletter/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_saves_to_db(self):
        payload = {"email": "newsletter@corp.com", "gdpr_consent": True}
        self.client.post("/api/v1/public/contact/newsletter/", payload, format="json")
        self.assertEqual(NewsletterSubscription.objects.count(), 1)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class ModelTests(TestCase):
    def test_demo_request_auto_reference(self):
        dr = DemoRequest.objects.create(
            full_name="Test User",
            email="test@company.com",
            product_interests=["CyMed"],
            gdpr_consent=True,
        )
        self.assertTrue(dr.reference_number.startswith("CYB-"))
        self.assertEqual(len(dr.reference_number), 10)

    def test_contact_message_auto_ticket(self):
        msg = ContactMessage.objects.create(
            full_name="Test User",
            email="test@company.com",
            subject="Test",
            message="Test message",
            gdpr_consent=True,
        )
        self.assertTrue(msg.ticket_number.startswith("TKT-"))

    def test_partner_application_auto_reference(self):
        app = PartnerApplication.objects.create(
            company_name="TechCo",
            contact_name="John",
            email="john@techco.com",
            partner_type="reseller",
            gdpr_consent=True,
        )
        self.assertTrue(app.reference_number.startswith("PAR-"))

    def test_website_api_log_immutable(self):
        from products.website.models import WebsiteApiLog
        from django.utils import timezone

        log = WebsiteApiLog.objects.create(
            endpoint="/api/v1/public/products/",
            method="GET",
            status_code=200,
        )
        with self.assertRaises(ValueError):
            log.save()
