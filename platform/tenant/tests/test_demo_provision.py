"""
Real end-to-end coverage for DemoProvisioningService.provision_demo() via
the public API — none existed before (confirmed: no prior test anywhere in
the repo exercised this path, despite it being live in production).
Covers: default (7-day) trial, the demo.cy-com.com sandbox override (3h),
and the hospital contact-required exclusion.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from platform.tenant.models import Tenant


@pytest.mark.django_db
class TestDemoProvisionAPI:
    def _client(self):
        return APIClient()

    def test_default_trial_creates_real_tenant_and_subscription(self):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            resp = self._client().post(
                "/api/v1/public/demo/provision/",
                {"product_code": "cymed_clinic", "email": "trial@example.com"},
                format="json",
            )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        tenant = Tenant.objects.get(slug=body["tenant_slug"])
        sub = tenant.subscriptions.first()
        assert sub is not None
        assert sub.is_trial is True
        trial_ends_at = datetime.fromisoformat(body["trial_ends_at"])
        hours_left = (trial_ends_at - timezone.now()).total_seconds() / 3600
        assert 166 <= hours_left <= 169  # ~7 days (DEMO_TRIAL_HOURS), not the 3h sandbox window
        assert tenant.metadata.get("is_demo") is True

    def test_sandbox_flag_shortens_trial_to_three_hours(self):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            resp = self._client().post(
                "/api/v1/public/demo/provision/",
                {"product_code": "cymed_clinic", "email": "sandbox@example.com", "sandbox": True},
                format="json",
            )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        tenant = Tenant.objects.get(slug=body["tenant_slug"])
        trial_ends_at = datetime.fromisoformat(body["trial_ends_at"])
        hours_left = (trial_ends_at - timezone.now()).total_seconds() / 3600
        assert 2.8 <= hours_left <= 3.1
        assert tenant.metadata.get("is_demo") is True

    def test_hospital_is_contact_required_not_provisioned(self):
        resp = self._client().post(
            "/api/v1/public/demo/provision/",
            {"product_code": "cymed_hospital", "email": "hospital@example.com"},
            format="json",
        )
        assert resp.status_code == 400, resp.content
        assert resp.json()["contact_required"] is True
