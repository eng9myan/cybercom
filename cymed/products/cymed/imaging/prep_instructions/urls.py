"""URL routes for the CyMed Imaging patient prep instructions sub-app."""
from __future__ import annotations

from django.urls import path

from .views import (
    ContrastConsentViewSet,
    PrepAssignmentViewSet,
    PrepChecklistItemViewSet,
    PrepTemplateViewSet,
)

urlpatterns = [
    path(
        "prep-templates/",
        PrepTemplateViewSet.as_view({"get": "list", "post": "create"}),
        name="prep-template-list",
    ),
    path(
        "prep-templates/<uuid:pk>/",
        PrepTemplateViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="prep-template-detail",
    ),
    path(
        "prep-templates/create-template/",
        PrepTemplateViewSet.as_view({"post": "create_template"}),
        name="prep-template-create-template",
    ),
    path(
        "prep-assignments/",
        PrepAssignmentViewSet.as_view({"get": "list", "post": "create"}),
        name="prep-assignment-list",
    ),
    path(
        "prep-assignments/<uuid:pk>/",
        PrepAssignmentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="prep-assignment-detail",
    ),
    path(
        "prep-assignments/assign/",
        PrepAssignmentViewSet.as_view({"post": "assign"}),
        name="prep-assignment-assign",
    ),
    path(
        "prep-assignments/<uuid:pk>/record-view/",
        PrepAssignmentViewSet.as_view({"post": "record_view"}),
        name="prep-assignment-record-view",
    ),
    path(
        "prep-assignments/<uuid:pk>/mark-item/",
        PrepAssignmentViewSet.as_view({"post": "mark_item"}),
        name="prep-assignment-mark-item",
    ),
    path(
        "prep-checklist-items/",
        PrepChecklistItemViewSet.as_view({"get": "list"}),
        name="prep-checklist-item-list",
    ),
    path(
        "prep-checklist-items/<uuid:pk>/",
        PrepChecklistItemViewSet.as_view({"get": "retrieve"}),
        name="prep-checklist-item-detail",
    ),
    path(
        "contrast-consents/",
        ContrastConsentViewSet.as_view({"get": "list", "post": "create"}),
        name="contrast-consent-list",
    ),
    path(
        "contrast-consents/<uuid:pk>/",
        ContrastConsentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="contrast-consent-detail",
    ),
    path(
        "contrast-consents/open/",
        ContrastConsentViewSet.as_view({"post": "open_consent"}),
        name="contrast-consent-open",
    ),
    path(
        "contrast-consents/<uuid:pk>/sign/",
        ContrastConsentViewSet.as_view({"post": "sign"}),
        name="contrast-consent-sign",
    ),
    path(
        "contrast-consents/<uuid:pk>/decline/",
        ContrastConsentViewSet.as_view({"post": "decline"}),
        name="contrast-consent-decline",
    ),
]
