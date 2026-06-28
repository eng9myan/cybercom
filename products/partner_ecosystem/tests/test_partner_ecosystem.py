import uuid
import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
import jwt

from products.partner_ecosystem.models import (
    Partner, PartnerApplication, PartnerCertification, LeadRegistration,
    MarketplaceExtension, PartnerPortalAccess
)

TENANT_A = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")


@pytest.fixture
def auth_client():
    client = APIClient()
    payload = {
        "sub": "33333333-3333-3333-3333-333333333333",
        "email": "admin@cybercom.io",
        "tenant_id": str(TENANT_A),
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(TENANT_A),
    )
    return client


@pytest.mark.django_db
class TestPartnerEcosystemAPIs:

    def test_partners(self, auth_client):
        # Create
        res = auth_client.post(
            "/api/v1/partners/partners/",
            {
                "name": "Global Tech Distributors",
                "code": "PART-GLOB-001",
                "partner_type": "strategic",
                "status": "prospect",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        partner_id = res.data["id"]

        # Certify
        res = auth_client.post(f"/api/v1/partners/partners/{partner_id}/certify/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "certified"

        # Suspend
        res = auth_client.post(f"/api/v1/partners/partners/{partner_id}/suspend/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "suspended"

    def test_partner_applications(self, auth_client):
        res = auth_client.post(
            "/api/v1/partners/applications/",
            {
                "partner_name": "NextGen Integrators",
                "partner_type": "implementation",
                "contact_name": "John Doe",
                "contact_email": "john@nextgen.com",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        app_id = res.data["id"]

        # Approve
        res = auth_client.post(
            f"/api/v1/partners/applications/{app_id}/approve/",
            {"reviewed_by_id": str(uuid.uuid4()), "review_notes": "Meets all criteria"},
            format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "approved"

        # Reject
        res = auth_client.post(
            f"/api/v1/partners/applications/{app_id}/reject/",
            {"reviewed_by_id": str(uuid.uuid4()), "review_notes": "Incomplete info"},
            format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "rejected"

    def test_partner_certifications(self, auth_client):
        partner = Partner.objects.create(
            tenant_id=TENANT_A,
            name="CareTech Services",
            code="PART-CARE-001",
            partner_type="strategic",
        )
        res = auth_client.post(
            "/api/v1/partners/certifications/",
            {
                "partner": partner.id,
                "product_code": "cymed_hospital",
                "certification_type": "technical",
                "status": "completed",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    def test_lead_registrations(self, auth_client):
        partner = Partner.objects.create(
            tenant_id=TENANT_A,
            name="CareTech Services",
            code="PART-CARE-002",
            partner_type="strategic",
        )
        res = auth_client.post(
            "/api/v1/partners/lead-registrations/",
            {
                "partner": partner.id,
                "lead_name": "Al Mafraq Hospital Group",
                "lead_email": "purchasing@mafraq.ae",
                "estimated_value": "250000.00",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        lead_id = res.data["id"]

        # Approve
        res = auth_client.post(
            f"/api/v1/partners/lead-registrations/{lead_id}/approve/",
            {"approved_by_id": str(uuid.uuid4())},
            format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "approved"

        # Convert
        res = auth_client.post(f"/api/v1/partners/lead-registrations/{lead_id}/convert/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "converted"

    def test_marketplace_extensions(self, auth_client):
        partner = Partner.objects.create(
            tenant_id=TENANT_A,
            name="CareTech Services",
            code="PART-CARE-003",
            partner_type="strategic",
        )
        res = auth_client.post(
            "/api/v1/partners/marketplace/",
            {
                "partner": partner.id,
                "extension_name": "SMS Gateway Gateway Custom",
                "code": "ext-sms-custom-alert",
                "category": "integration",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        ext_id = res.data["id"]

        # Publish
        res = auth_client.post(f"/api/v1/partners/marketplace/{ext_id}/publish/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "published"

        # Deprecate
        res = auth_client.post(f"/api/v1/partners/marketplace/{ext_id}/deprecate/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "deprecated"

        # Record Install
        res = auth_client.post(f"/api/v1/partners/marketplace/{ext_id}/record_install/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["install_count"] == 1

    def test_partner_portal_access(self, auth_client):
        partner = Partner.objects.create(
            tenant_id=TENANT_A,
            name="CareTech Services",
            code="PART-CARE-004",
            partner_type="strategic",
        )
        res = auth_client.post(
            "/api/v1/partners/portal-access/",
            {
                "partner": partner.id,
                "user_id": str(uuid.uuid4()),
                "access_level": "admin",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
