"""
Tests for CyMed Commercial — Usage Metering and Deployment Profiles.
"""
import uuid
from decimal import Decimal
import pytest
from unittest.mock import patch

from products.cymed.commercial.usage_metering.models import UsageMeter, UsageAlert
from products.cymed.commercial.usage_metering.services import UsageMeteringService
from products.cymed.commercial.deployment_profiles.models import (
    DeploymentProfile, DeploymentConfiguration, DeploymentCapability
)

TENANT = uuid.UUID("10000000-0000-0000-0000-000000000001")


@pytest.fixture
def deployment_profile(db):
    return DeploymentProfile.objects.create(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        code="saas_test",
        name="SaaS Test",
        profile_type="saas",
        requires_offline_license=False,
        supports_auto_update=True,
        supports_telemetry=True,
        requires_government_clearance=False,
    )


class TestDeploymentProfileModel:
    def test_str(self, deployment_profile):
        assert "saas_test" in str(deployment_profile)
        assert "saas" in str(deployment_profile)

    def test_saas_no_offline_requirement(self, deployment_profile):
        assert deployment_profile.requires_offline_license is False

    def test_capabilities(self, db, deployment_profile):
        cap = DeploymentCapability.objects.create(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            profile=deployment_profile,
            capability_code="online_activation",
            is_supported=True,
        )
        assert cap.is_supported is True

    def test_air_gapped_profile_requirements(self, db):
        ag = DeploymentProfile.objects.create(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            code="air_gapped_test",
            name="Air-Gapped Test",
            profile_type="air_gapped",
            requires_offline_license=True,
            supports_auto_update=False,
            supports_telemetry=False,
            requires_government_clearance=True,
        )
        assert ag.requires_offline_license is True
        assert ag.supports_auto_update is False
        assert ag.requires_government_clearance is True


class TestUsageMeteringService:
    @patch("products.cymed.commercial.usage_metering.services.License")
    def test_record_snapshot(self, mock_license_cls, db):
        from django.core.exceptions import ObjectDoesNotExist
        mock_license_cls.objects.get.side_effect = ObjectDoesNotExist("No license")
        meter = UsageMeteringService.record_snapshot(
            tenant_id=TENANT,
            product_code="cymed_clinic",
            edition_code="starter",
            metrics={
                "active_users": 5,
                "active_providers": 2,
                "api_calls": 1000,
                "storage_gb": Decimal("2.5"),
            },
        )
        assert meter.active_users == 5
        assert meter.api_calls == 1000

    @patch("products.cymed.commercial.usage_metering.services.License")
    def test_snapshot_idempotent_today(self, mock_license_cls, db):
        from django.core.exceptions import ObjectDoesNotExist
        mock_license_cls.objects.get.side_effect = ObjectDoesNotExist("No license")
        UsageMeteringService.record_snapshot(
            tenant_id=TENANT,
            product_code="cymed_clinic",
            edition_code="starter",
            metrics={"active_users": 3},
        )
        UsageMeteringService.record_snapshot(
            tenant_id=TENANT,
            product_code="cymed_clinic",
            edition_code="starter",
            metrics={"active_users": 7},
        )
        count = UsageMeter.objects.filter(tenant_id=TENANT, product_code="cymed_clinic").count()
        assert count == 1
        meter = UsageMeter.objects.get(tenant_id=TENANT, product_code="cymed_clinic")
        assert meter.active_users == 7

    def test_usage_alert_model(self, db):
        meter = UsageMeter.objects.create(
            tenant_id=TENANT,
            snapshot_date="2026-06-23",
            product_code="cymed_hospital",
            active_users=50,
            api_calls=10000,
        )
        alert = UsageAlert.objects.create(
            tenant_id=TENANT,
            meter=meter,
            alert_type="over_limit",
            severity="critical",
            resource="users",
            current_value=50,
            limit_value=20,
            percentage_used=Decimal("250.00"),
        )
        assert alert.severity == "critical"
        assert alert.is_resolved is False
