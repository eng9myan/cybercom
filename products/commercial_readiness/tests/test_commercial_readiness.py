import datetime
import uuid
import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
import jwt

from products.commercial_readiness.models import (
    PricingPlan, Quotation, Proposal, LicenseKey,
    ComplianceCertification, CompetitiveBenchmark,
    License, Subscription, ProductEdition, FeatureFlag,
    TenantFeatureFlagOverride, WhiteLabelConfig, ConcurrentLicenseSession,
    CustomerPortalAccess, SupportTicket, MarketplaceListing,
    MarketplaceInstallation, CommercialMetricsSnapshot
)

TENANT_A = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Unit tests — pure model logic, no database required
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLicenseModelProperties:

    def _make_license(self, valid_until=None, grace_period_days=30):
        lic = License.__new__(License)
        lic.valid_until = valid_until
        lic.grace_period_days = grace_period_days
        lic.license_key = "LIC-UNIT-TEST"
        lic.product_code = "cymed_clinic"
        lic.max_users = 50
        lic.licensed_features = ["appointments", "emr", "lab"]
        return lic

    def test_is_expired_true_when_past_valid_until(self):
        lic = self._make_license(valid_until=timezone.now() - datetime.timedelta(days=1))
        assert lic.is_expired is True

    def test_is_expired_false_when_valid_until_in_future(self):
        lic = self._make_license(valid_until=timezone.now() + datetime.timedelta(days=90))
        assert lic.is_expired is False

    def test_is_expired_false_when_no_valid_until(self):
        lic = self._make_license(valid_until=None)
        assert lic.is_expired is False

    def test_is_in_grace_period_true_when_recently_expired(self):
        lic = self._make_license(
            valid_until=timezone.now() - datetime.timedelta(hours=12),
            grace_period_days=30,
        )
        assert lic.is_in_grace_period is True

    def test_is_in_grace_period_false_when_well_past_grace(self):
        lic = self._make_license(
            valid_until=timezone.now() - datetime.timedelta(days=60),
            grace_period_days=30,
        )
        assert lic.is_in_grace_period is False

    def test_is_in_grace_period_false_when_still_active(self):
        lic = self._make_license(valid_until=timezone.now() + datetime.timedelta(days=1))
        assert lic.is_in_grace_period is False

    def test_is_in_grace_period_false_when_no_valid_until(self):
        lic = self._make_license(valid_until=None)
        assert lic.is_in_grace_period is False

    def test_generate_offline_token_returns_64_char_sha256_hex(self):
        lic = self._make_license(valid_until=timezone.now() + datetime.timedelta(days=365))
        token = lic.generate_offline_token()
        assert len(token) == 64
        assert all(c in "0123456789abcdef" for c in token)

    def test_generate_offline_token_sets_offline_token_attribute(self):
        lic = self._make_license()
        token = lic.generate_offline_token()
        assert lic.offline_token == token

    def test_generate_offline_token_deterministic(self):
        lic = self._make_license(valid_until=None)
        t1 = lic.generate_offline_token()
        t2 = lic.generate_offline_token()
        assert t1 == t2

    def test_generate_offline_token_differs_by_product(self):
        lic1 = self._make_license()
        lic2 = self._make_license()
        lic2.product_code = "cymed_hospital"
        assert lic1.generate_offline_token() != lic2.generate_offline_token()

    def test_generate_offline_token_sorts_features(self):
        lic_a = self._make_license()
        lic_a.licensed_features = ["emr", "appointments", "lab"]
        lic_b = self._make_license()
        lic_b.licensed_features = ["appointments", "emr", "lab"]
        assert lic_a.generate_offline_token() == lic_b.generate_offline_token()


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
class TestCommercialReadinessAPIs:

    def test_pricing_plans(self, auth_client):
        # Create
        res = auth_client.post(
            "/api/v1/commercial-readiness/pricing-plans/",
            {
                "name": "Standard User Plan",
                "code": "PLAN-STD-001",
                "product_code": "cymed_clinic",
                "plan_type": "per_user",
                "base_price": "50.00",
                "billing_cycle": "monthly",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        plan_id = res.data["id"]

        # List
        res = auth_client.get("/api/v1/commercial-readiness/pricing-plans/")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data["results"]) == 1

        # Retrieve
        res = auth_client.get(f"/api/v1/commercial-readiness/pricing-plans/{plan_id}/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["code"] == "PLAN-STD-001"

    def test_quotations(self, auth_client):
        # Create
        res = auth_client.post(
            "/api/v1/commercial-readiness/quotations/",
            {
                "quote_number": "Q-2026-001",
                "customer_name": "Jordan Medical Group",
                "customer_email": "info@jmg.jo",
                "total": "12000.00",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        quote_id = res.data["id"]

        # Send
        res = auth_client.post(f"/api/v1/commercial-readiness/quotations/{quote_id}/send/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "sent"

        # Accept
        res = auth_client.post(f"/api/v1/commercial-readiness/quotations/{quote_id}/accept/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "accepted"

        # Reject
        res = auth_client.post(f"/api/v1/commercial-readiness/quotations/{quote_id}/reject/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "rejected"

    def test_proposals(self, auth_client):
        # Create
        res = auth_client.post(
            "/api/v1/commercial-readiness/proposals/",
            {
                "opportunity_id": "OPP-9921",
                "customer_name": "Saudi Health Ministry",
                "proposal_title": "CyMed Core Implementation for MOH Hospitals",
                "total_value": "450000.00",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        prop_id = res.data["id"]

        # Submit
        res = auth_client.post(f"/api/v1/commercial-readiness/proposals/{prop_id}/submit/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "submitted"

        # Mark Won
        res = auth_client.post(
            f"/api/v1/commercial-readiness/proposals/{prop_id}/mark_won/",
            {"win_reason": "Better regional localization and CBAHI compliance support"},
            format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "won"

        # Mark Lost
        res = auth_client.post(
            f"/api/v1/commercial-readiness/proposals/{prop_id}/mark_lost/",
            {"loss_reason": "Budget constraints"},
            format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "lost"

    def test_license_keys(self, auth_client):
        res = auth_client.post(
            "/api/v1/commercial-readiness/license-keys/",
            {
                "customer_id": str(uuid.uuid4()),
                "product_code": "cymed_hospital",
                "key_value": "KEY-HOSP-TEST-XYZ",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        key_id = res.data["id"]

        # Activate
        res = auth_client.post(f"/api/v1/commercial-readiness/license-keys/{key_id}/activate/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["is_active"] is True

        # Deactivate
        res = auth_client.post(f"/api/v1/commercial-readiness/license-keys/{key_id}/deactivate/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["is_active"] is False

    def test_compliance_certifications(self, auth_client):
        res = auth_client.post(
            "/api/v1/commercial-readiness/compliance-certifications/",
            {
                "product_code": "cymed_core",
                "standard": "hipaa",
                "status": "certified",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    def test_competitive_benchmarks(self, auth_client):
        res = auth_client.post(
            "/api/v1/commercial-readiness/benchmarks/",
            {
                "product_code": "cymed_rcm",
                "competitor_name": "Epic Systems",
                "category": "pricing",
                "our_score": "9.5",
                "competitor_score": "6.0",
                "last_updated": "2026-06-28",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    def test_licenses(self, auth_client):
        res = auth_client.post(
            "/api/v1/commercial-readiness/licenses/",
            {
                "product_code": "cymed_clinic",
                "license_key": "LIC-CLINIC-XYZ",
                "issued_to": "Amman Clinic",
                "issued_to_email": "amman@clinic.jo",
                "valid_from": timezone.now().isoformat(),
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        lic_id = res.data["id"]

        # Activate
        res = auth_client.post(f"/api/v1/commercial-readiness/licenses/{lic_id}/activate/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "activated"

        # Deactivate
        res = auth_client.post(f"/api/v1/commercial-readiness/licenses/{lic_id}/deactivate/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "suspended"

        # Renew
        res = auth_client.post(f"/api/v1/commercial-readiness/licenses/{lic_id}/renew/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "renewed"

        # Suspend
        res = auth_client.post(f"/api/v1/commercial-readiness/licenses/{lic_id}/suspend/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "suspended"

        # Generate Offline Token
        res = auth_client.post(f"/api/v1/commercial-readiness/licenses/{lic_id}/generate_offline_token/")
        assert res.status_code == status.HTTP_200_OK
        assert "offline_token" in res.data

    def test_subscriptions(self, auth_client):
        # Create base license
        lic = License.objects.create(
            tenant_id=TENANT_A,
            product_code="cymed_clinic",
            license_key="LIC-SUB-TEST",
            issued_to="Subscriber Clinic",
            issued_to_email="sub@clinic.com",
            valid_from=timezone.now(),
        )

        res = auth_client.post(
            "/api/v1/commercial-readiness/subscriptions/",
            {
                "license": lic.id,
                "current_period_start": "2026-06-01",
                "current_period_end": "2026-06-30",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        sub_id = res.data["id"]

        # Cancel
        res = auth_client.post(f"/api/v1/commercial-readiness/subscriptions/{sub_id}/cancel/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "cancellation_scheduled"

        # Resume
        res = auth_client.post(f"/api/v1/commercial-readiness/subscriptions/{sub_id}/resume/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "resumed"

    def test_product_editions(self, auth_client):
        # Create ProductEdition directly since endpoint is read-only
        ProductEdition.objects.create(
            product_code="cymed_clinic",
            edition_code="starter",
            name="Starter Edition",
            is_active=True,
        )
        res = auth_client.get("/api/v1/commercial-readiness/product-editions/")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data["results"]) == 1

    def test_feature_flags(self, auth_client):
        FeatureFlag.objects.create(
            product_code="cymed_clinic",
            flag_key="clinic.appointments",
            flag_name="Appointments Module",
            is_enabled=True,
        )
        res = auth_client.get("/api/v1/commercial-readiness/feature-flags/")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data["results"]) == 1

    def test_tenant_feature_flag_overrides(self, auth_client):
        flag = FeatureFlag.objects.create(
            product_code="cymed_clinic",
            flag_key="clinic.telemedicine",
            flag_name="Telemedicine Module",
            is_enabled=False,
        )
        res = auth_client.post(
            "/api/v1/commercial-readiness/feature-flag-overrides/",
            {
                "flag": flag.id,
                "is_enabled": True,
                "override_reason": "Enterprise customer request",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    def test_white_label_configs(self, auth_client):
        res = auth_client.post(
            "/api/v1/commercial-readiness/white-label-configs/",
            {
                "tenant_name": "Seha Hospital Group",
                "display_name": "Seha Care",
                "primary_color": "#0055A5",
                "secondary_color": "#004B91",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    def test_concurrent_sessions(self, auth_client):
        lic = License.objects.create(
            tenant_id=TENANT_A,
            product_code="cymed_clinic",
            license_key="LIC-CONC-TEST",
            issued_to="Conc Clinic",
            issued_to_email="conc@clinic.com",
            valid_from=timezone.now(),
        )
        res = auth_client.post(
            "/api/v1/commercial-readiness/concurrent-sessions/",
            {
                "license": lic.id,
                "user_id": str(uuid.uuid4()),
                "is_active": True,
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        sess_id = res.data["id"]

        # Checkout
        res = auth_client.post(f"/api/v1/commercial-readiness/concurrent-sessions/{sess_id}/checkout/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "checked_out"

        # Checkin
        res = auth_client.post(f"/api/v1/commercial-readiness/concurrent-sessions/{sess_id}/checkin/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "checked_in"

    def test_customer_portal_access(self, auth_client):
        res = auth_client.post(
            "/api/v1/commercial-readiness/portal-access/",
            {
                "user_id": str(uuid.uuid4()),
                "access_level": "admin",
                "can_manage_licenses": True,
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    def test_support_tickets(self, auth_client):
        res = auth_client.post(
            "/api/v1/commercial-readiness/support-tickets/",
            {
                "subject": "System is slow during peak clinic hours",
                "description": "Patients loading takes up to 5 seconds.",
                "product_code": "cymed_clinic",
                "priority": "high",
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED
        ticket_id = res.data["id"]

        # Assign
        res = auth_client.post(
            f"/api/v1/commercial-readiness/support-tickets/{ticket_id}/assign/",
            {"assigned_to_id": str(uuid.uuid4())},
            format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "assigned"

        # Resolve
        res = auth_client.post(
            f"/api/v1/commercial-readiness/support-tickets/{ticket_id}/resolve/",
            {"resolution_notes": "Added database indexes for query optimization"},
            format="json"
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "resolved"

        # Close
        res = auth_client.post(f"/api/v1/commercial-readiness/support-tickets/{ticket_id}/close/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "closed"

    def test_marketplace_listings(self, auth_client):
        listing = MarketplaceListing.objects.create(
            code="ext-telemed-custom",
            name="Custom Telemedicine Connect",
            category="connector",
            price_model="free",
            status="published",
        )

        # Install
        res = auth_client.post(f"/api/v1/commercial-readiness/marketplace-listings/{listing.id}/install/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "installed"

    def test_marketplace_installations(self, auth_client):
        listing = MarketplaceListing.objects.create(
            code="ext-whatsapp-alert",
            name="WhatsApp Notifications Alert",
            category="extension",
            price_model="free",
            status="published",
        )
        res = auth_client.post(
            "/api/v1/commercial-readiness/marketplace-installations/",
            {
                "listing": listing.id,
                "installed_by_id": str(uuid.uuid4()),
                "is_active": True,
            },
            format="json"
        )
        assert res.status_code == status.HTTP_201_CREATED

    def test_metrics_snapshots(self, auth_client):
        CommercialMetricsSnapshot.objects.create(
            snapshot_date="2026-06-28",
            metric_type="arr",
            product_code="cymed_clinic",
            value="150000.00",
        )
        res = auth_client.get("/api/v1/commercial-readiness/metrics-snapshots/")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data["results"]) == 1
