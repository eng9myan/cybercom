"""
Website Public API — URL routes.
All under /api/v1/public/ as registered in core/urls.py.
"""

from django.urls import path

from .views import (
    CaseStudyDetailView,
    CaseStudyListView,
    ContactCreateView,
    ContactStatusView,
    DemoRequestCreateView,
    DemoRequestStatusView,
    DocumentationSearchView,
    DocumentationSectionDetailView,
    DocumentationSectionListView,
    IndustryDetailView,
    IndustryListView,
    NewsletterSubscribeView,
    PartnerApplicationCreateView,
    PartnerListView,
    ProductDetailView,
    ProductListView,
    PublicHealthView,
)

app_name = "website"

urlpatterns = [
    # Health
    path("health/", PublicHealthView.as_view(), name="health"),
    # Products
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    # Industries
    path("industries/", IndustryListView.as_view(), name="industry-list"),
    path("industries/<slug:slug>/", IndustryDetailView.as_view(), name="industry-detail"),
    # Case Studies
    path("case-studies/", CaseStudyListView.as_view(), name="case-study-list"),
    path("case-studies/<slug:slug>/", CaseStudyDetailView.as_view(), name="case-study-detail"),
    # Partners — directory + application
    path("partners/", PartnerListView.as_view(), name="partner-list"),
    path("partners/apply/", PartnerApplicationCreateView.as_view(), name="partner-apply"),
    # Documentation
    path("documentation/", DocumentationSectionListView.as_view(), name="doc-section-list"),
    path("documentation/search/", DocumentationSearchView.as_view(), name="doc-search"),
    path(
        "documentation/<slug:slug>/",
        DocumentationSectionDetailView.as_view(),
        name="doc-section-detail",
    ),
    # Demo Request
    path("demo-request/", DemoRequestCreateView.as_view(), name="demo-request-create"),
    path(
        "demo-request/<str:reference_number>/status/",
        DemoRequestStatusView.as_view(),
        name="demo-request-status",
    ),
    # Contact
    path("contact/", ContactCreateView.as_view(), name="contact-create"),
    path("contact/newsletter/", NewsletterSubscribeView.as_view(), name="newsletter-subscribe"),
    path("contact/<str:ticket_number>/status/", ContactStatusView.as_view(), name="contact-status"),
]
