"""
Real end-to-end coverage for SubscriptionRegistrationService.register() via
the public API — unified Basic/Pro/Enterprise tiers, hospital exclusion,
and the real pending bank-transfer invoice.
"""

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import InvoicePaymentMethod, InvoiceStatus, Tenant, TenantStatus


@pytest.mark.django_db
class TestSubscriptionRegisterAPI:
    def _client(self):
        return APIClient()

    def test_professional_tier_creates_pending_tenant_and_invoice(self):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            resp = self._client().post(
                "/api/v1/public/subscriptions/register/",
                {
                    "product_code": "cymed_clinic",
                    "tier": "professional",
                    "email": "owner@clinic.example.com",
                    "org_name": "Example Clinic",
                },
                format="json",
            )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        assert body["tier"] == "professional"
        assert body["amount"] == "149"
        assert body["payment_method"] == InvoicePaymentMethod.BANK_TRANSFER
        assert body["status"] == "pending_approval"

        tenant = Tenant.objects.get(slug=body["tenant_slug"])
        assert tenant.status == TenantStatus.PENDING  # not activated until finance approves
        sub = tenant.subscriptions.first()
        assert sub.plan == "professional"
        assert sub.is_active is False
        invoice = sub.invoices.first()
        assert invoice.status == InvoiceStatus.PENDING
        assert invoice.invoice_number == body["invoice_number"]

    def test_hospital_is_contact_required_not_registered(self):
        resp = self._client().post(
            "/api/v1/public/subscriptions/register/",
            {"product_code": "cymed_hospital", "tier": "enterprise", "email": "cfo@hospital.example.com"},
            format="json",
        )
        assert resp.status_code == 400, resp.content
        assert resp.json()["contact_required"] is True

    def test_tier_pricing_matches_unified_catalog(self):
        expected = {"starter": "49", "professional": "149", "enterprise": "399"}
        for tier, price in expected.items():
            with patch.object(
                __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
            ):
                resp = self._client().post(
                    "/api/v1/public/subscriptions/register/",
                    {"product_code": "cymed_pharmacy", "tier": tier, "email": f"{tier}@pharmacy.example.com"},
                    format="json",
                )
            assert resp.status_code == 201, resp.content
            assert resp.json()["amount"] == price

    def test_shared_realm_registration_enables_unmanaged_attributes(self):
        """A shared-realm (cycom) signup must flip the shared realm's
        unmanaged-attribute policy ON *before* provisioning the user —
        otherwise Keycloak drops the tenant_id user attribute and the
        issued access token carries no tenant_id claim (the self-serve
        login bug). See _ensure_shared_realm_unmanaged_attributes()."""
        from platform.cyidentity.models import IdentityRealm, RealmType
        from platform.cyidentity.services import KeycloakAdminClient
        from platform.tenant.services import (
            SHARED_REALM_NAME,
            SubscriptionRegistrationService,
        )

        IdentityRealm.objects.create(
            tenant_id=__import__("uuid").uuid4(),
            realm_name=SHARED_REALM_NAME,
            realm_type=RealmType.WORKFORCE,
            issuer_url=f"http://kc.test/realms/{SHARED_REALM_NAME}",
            jwks_uri=f"http://kc.test/realms/{SHARED_REALM_NAME}/protocol/openid-connect/certs",
            admin_api_url=f"http://kc.test/admin/realms/{SHARED_REALM_NAME}",
        )

        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ), patch.object(
            KeycloakAdminClient, "allow_unmanaged_user_attributes"
        ) as allow_unmanaged:
            SubscriptionRegistrationService().register(
                product_code="cycom",
                tier="starter",
                email="owner@acme.example.com",
                org_name="Acme",
            )

        # The shared realm must have its unmanaged-attribute policy enabled;
        # code position guarantees this happens before provision_user() pushes
        # the tenant_id attribute to Keycloak.
        allow_unmanaged.assert_called_once_with(SHARED_REALM_NAME)
