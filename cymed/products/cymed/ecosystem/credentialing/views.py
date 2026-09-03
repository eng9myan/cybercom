"""ViewSets and action endpoints for credentialing sub-app."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import (
    CredentialDocument,
    CredentialingApplication,
    LicenseVerification,
    PrivilegeGrant,
)
from .serializers import (
    CredentialDocumentSerializer,
    CredentialingApplicationSerializer,
    LicenseVerificationSerializer,
    PrivilegeGrantSerializer,
)


class CredentialingApplicationViewSet(viewsets.ModelViewSet):
    queryset = CredentialingApplication.objects.all()
    serializer_class = CredentialingApplicationSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open(self, request: Request) -> Response:
        data = request.data
        app = services.open_application(
            tenant_id=data["tenant_id"],
            subject_kind=data["subject_kind"],
            facility_id=data.get("facility_id"),
            practitioner_id=data.get("practitioner_id"),
            submitted_by_profile_id=data.get("submitted_by_profile_id"),
            target_networks=data.get("target_networks"),
        )
        return Response(CredentialingApplicationSerializer(app).data)

    @action(detail=True, methods=["post"], url_path="request-info")
    def request_info(self, request: Request, pk: str | None = None) -> Response:
        app = services.request_more_info(
            application_id=pk,
            note=request.data.get("note", ""),
        )
        return Response(CredentialingApplicationSerializer(app).data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request: Request, pk: str | None = None) -> Response:
        app = services.approve_application(
            application_id=pk,
            decided_by_profile_id=request.data.get("decided_by_profile_id"),
            decision_reason=request.data.get("decision_reason", ""),
            expires_at=request.data.get("expires_at"),
        )
        return Response(CredentialingApplicationSerializer(app).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request: Request, pk: str | None = None) -> Response:
        app = services.reject_application(
            application_id=pk,
            decision_reason=request.data.get("decision_reason", ""),
        )
        return Response(CredentialingApplicationSerializer(app).data)


class CredentialDocumentViewSet(viewsets.ModelViewSet):
    queryset = CredentialDocument.objects.all()
    serializer_class = CredentialDocumentSerializer

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request: Request) -> Response:
        data = request.data
        doc = services.upload_document(
            application_id=data["application_id"],
            kind=data["kind"],
            file_url=data.get("file_url", ""),
            expires_at=data.get("expires_at"),
        )
        return Response(CredentialDocumentSerializer(doc).data)


class LicenseVerificationViewSet(viewsets.ModelViewSet):
    queryset = LicenseVerification.objects.all()
    serializer_class = LicenseVerificationSerializer

    @action(detail=False, methods=["post"], url_path="verify")
    def verify(self, request: Request) -> Response:
        data = request.data
        ver = services.verify_license(
            document_id=data.get("document_id"),
            issuing_authority=data["issuing_authority"],
            license_number=data["license_number"],
            jurisdiction=data["jurisdiction"],
            verification_kind=data.get("verification_kind", "automated_registry"),
            raw_response=data.get("raw_response"),
        )
        return Response(LicenseVerificationSerializer(ver).data)


class PrivilegeGrantViewSet(viewsets.ModelViewSet):
    queryset = PrivilegeGrant.objects.all()
    serializer_class = PrivilegeGrantSerializer

    @action(detail=False, methods=["post"], url_path="grant")
    def grant(self, request: Request) -> Response:
        data = request.data
        grant = services.grant_privileges(
            application_id=data.get("application_id"),
            tenant_id=data["tenant_id"],
            subject_kind=data["subject_kind"],
            facility_id=data.get("facility_id"),
            practitioner_id=data.get("practitioner_id"),
            privilege_scope=data.get("privilege_scope", []),
            granted_by_profile_id=data.get("granted_by_profile_id"),
            expires_at=data.get("expires_at"),
        )
        return Response(PrivilegeGrantSerializer(grant).data)

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request: Request, pk: str | None = None) -> Response:
        grant = services.revoke_privileges(
            grant_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(PrivilegeGrantSerializer(grant).data)
