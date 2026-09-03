"""URL routing for credentialing sub-app."""
from __future__ import annotations

from django.urls import path

from .views import (
    CredentialDocumentViewSet,
    CredentialingApplicationViewSet,
    LicenseVerificationViewSet,
    PrivilegeGrantViewSet,
)


application_list = CredentialingApplicationViewSet.as_view({"get": "list", "post": "create"})
application_detail = CredentialingApplicationViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
application_open = CredentialingApplicationViewSet.as_view({"post": "open"})
application_request_info = CredentialingApplicationViewSet.as_view({"post": "request_info"})
application_approve = CredentialingApplicationViewSet.as_view({"post": "approve"})
application_reject = CredentialingApplicationViewSet.as_view({"post": "reject"})

document_list = CredentialDocumentViewSet.as_view({"get": "list", "post": "create"})
document_detail = CredentialDocumentViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
document_upload = CredentialDocumentViewSet.as_view({"post": "upload"})

verification_list = LicenseVerificationViewSet.as_view({"get": "list", "post": "create"})
verification_detail = LicenseVerificationViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
verification_verify = LicenseVerificationViewSet.as_view({"post": "verify"})

grant_list = PrivilegeGrantViewSet.as_view({"get": "list", "post": "create"})
grant_detail = PrivilegeGrantViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
grant_grant = PrivilegeGrantViewSet.as_view({"post": "grant"})
grant_revoke = PrivilegeGrantViewSet.as_view({"post": "revoke"})


urlpatterns = [
    path("applications/", application_list, name="credentialing-application-list"),
    path("applications/open/", application_open, name="credentialing-application-open"),
    path("applications/<uuid:pk>/", application_detail, name="credentialing-application-detail"),
    path("applications/<uuid:pk>/request-info/", application_request_info, name="credentialing-application-request-info"),
    path("applications/<uuid:pk>/approve/", application_approve, name="credentialing-application-approve"),
    path("applications/<uuid:pk>/reject/", application_reject, name="credentialing-application-reject"),
    path("documents/", document_list, name="credentialing-document-list"),
    path("documents/upload/", document_upload, name="credentialing-document-upload"),
    path("documents/<uuid:pk>/", document_detail, name="credentialing-document-detail"),
    path("verifications/", verification_list, name="credentialing-verification-list"),
    path("verifications/verify/", verification_verify, name="credentialing-verification-verify"),
    path("verifications/<uuid:pk>/", verification_detail, name="credentialing-verification-detail"),
    path("grants/", grant_list, name="credentialing-grant-list"),
    path("grants/grant/", grant_grant, name="credentialing-grant-grant"),
    path("grants/<uuid:pk>/", grant_detail, name="credentialing-grant-detail"),
    path("grants/<uuid:pk>/revoke/", grant_revoke, name="credentialing-grant-revoke"),
]
