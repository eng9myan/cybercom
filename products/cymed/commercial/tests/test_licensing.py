"""
Tests for CyMed Commercial — Licensing Engine.
Covers: models, services, API endpoints, offline activation, compliance.
"""
import uuid
import hashlib
import hmac
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from products.cymed.commercial.licensing.models import (
    License, LicenseKey, LicenseActivation, LicenseAudit,
    LicenseUsage, LicenseServer, OfflineActivationPackage
)
from products.cymed.commercial.licensing.services import LicensingService

TENANT = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")


@pytest.fixture
def license_obj(db):
    return License.objects.create(
        tenant_id=TENANT,
        license_number="CYM-TEST-0001",
        product_code="cymed_clinic",
        edition_code="starter",
        license_type="subscription",
        delivery_mode="online",
        organization_name="Test Clinic",
        country_code="JO",
        valid_from=date.today(),
        valid_until=date.today() + timedelta(days=365),
        max_users=10,
        max_providers=5,
        max_beds=0,
        status="active",
    )


@pytest.fixture
def license_key(db, license_obj):
    return LicenseKey.objects.create(
        tenant_id=TENANT,
        license=license_obj,
        key_string="AAAAA-BBBBB-CCCCC-DDDDD-EEEEE",
        max_activations=3,
    )


class TestLicenseModel:
    def test_is_valid_active(self, license_obj):
        assert license_obj.is_valid() is True

    def test_is_valid_expired(self, license_obj):
        license_obj.valid_until = date.today() - timedelta(days=30)
        license_obj.status = "expired"
        license_obj.save()
        assert license_obj.is_valid() is False

    def test_is_valid_revoked(self, license_obj):
        license_obj.status = "revoked"
        license_obj.save()
        assert license_obj.is_valid() is False

    def test_grace_period(self, license_obj):
        license_obj.valid_until = date.today() - timedelta(days=5)
        license_obj.grace_period_days = 14
        license_obj.status = "active"
        license_obj.save()
        assert license_obj.is_valid() is True

    def test_beyond_grace_period(self, license_obj):
        license_obj.valid_until = date.today() - timedelta(days=20)
        license_obj.grace_period_days = 14
        license_obj.status = "active"
        license_obj.save()
        assert license_obj.is_valid() is False

    def test_perpetual_license(self, license_obj):
        license_obj.valid_until = None
        license_obj.save()
        assert license_obj.is_valid() is True

    def test_str(self, license_obj):
        assert "CYM-TEST-0001" in str(license_obj)
        assert "Test Clinic" in str(license_obj)


class TestLicenseKeyModel:
    def test_can_activate(self, license_key):
        assert license_key.can_activate() is True

    def test_cannot_activate_revoked(self, license_key):
        license_key.is_revoked = True
        license_key.save()
        assert license_key.can_activate() is False

    def test_cannot_activate_max_reached(self, license_key):
        license_key.activation_count = 3
        license_key.save()
        assert license_key.can_activate() is False


class TestLicensingService:
    def test_generate_license_number(self):
        num = LicensingService.generate_license_number("cymed_clinic", "starter")
        assert num.startswith("CYM-")
        assert len(num) > 10

    def test_generate_key_string(self):
        key = LicensingService.generate_key_string("CYM-TEST-0001", 0)
        parts = key.split("-")
        assert len(parts) == 5

    def test_check_compliance_active(self, license_obj):
        result = LicensingService.check_compliance(license_obj)
        assert result["is_valid"] is True
        assert result["in_grace_period"] is False
        assert result["days_remaining"] > 0

    def test_check_compliance_grace(self, license_obj):
        license_obj.valid_until = date.today() - timedelta(days=5)
        license_obj.grace_period_days = 14
        license_obj.save()
        result = LicensingService.check_compliance(license_obj)
        assert result["in_grace_period"] is True

    def test_record_usage_snapshot(self, license_obj):
        usage = LicensingService.record_usage_snapshot(license_obj, {
            "active_users": 5,
            "active_providers": 2,
            "active_beds": 0,
            "api_calls": 100,
        })
        assert usage.active_users == 5
        assert usage.is_over_limit is False

    def test_record_usage_over_limit(self, license_obj):
        usage = LicensingService.record_usage_snapshot(license_obj, {
            "active_users": 15,  # max is 10
        })
        assert usage.is_over_limit is True

    def test_renew_license(self, license_obj):
        new_date = date.today() + timedelta(days=730)
        updated = LicensingService.renew_license(license_obj, new_date)
        assert updated.valid_until == new_date
        assert updated.status == "active"
        audit = LicenseAudit.objects.filter(license=license_obj, event_type="renewed").first()
        assert audit is not None

    def test_create_offline_package(self, license_obj):
        with patch("products.cymed.commercial.licensing.services.settings") as mock_settings:
            mock_settings.LICENSE_SIGNING_SECRET = "test-secret"
            pkg = LicensingService.create_offline_package(license_obj, "machine-fp-001")
        assert pkg.machine_fingerprint == "machine-fp-001"
        assert pkg.signed_payload != ""
        assert pkg.is_consumed is False
