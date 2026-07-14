import uuid

import pytest
from django.core.exceptions import ValidationError

from products.cydrive.fleet.models import DeliveryCompany, NetworkStatus


@pytest.mark.django_db
class TestNetworkMembership:
    """
    CyberCom master spec critical test cases 7 and 8:
      7. "A CyDrive company can use CyDrive without joining CyMart."
      8. "A suspended delivery-network membership does not cancel the
         CyDrive SaaS subscription."
    """

    def _company(self, **overrides):
        defaults = dict(tenant_id=uuid.uuid4(), name="Fast Wheels Delivery")
        defaults.update(overrides)
        return DeliveryCompany.objects.create(**defaults)

    def test_new_company_defaults_to_standalone_only(self):
        company = self._company()
        assert company.network_status == NetworkStatus.STANDALONE_ONLY
        assert company.is_network_eligible_for_jobs is False

    def test_company_can_operate_standalone_indefinitely(self):
        # No network application ever made — subscription still active,
        # nothing about using CyDrive forces a network decision.
        company = self._company()
        assert company.cydrive_subscription_active is True
        assert company.network_status == NetworkStatus.STANDALONE_ONLY

    def test_full_network_onboarding_flow(self):
        company = self._company()
        company.apply_to_network()
        assert company.network_status == NetworkStatus.NETWORK_APPLICATION_PENDING

        company.approve_network_membership()
        assert company.network_status == NetworkStatus.NETWORK_APPROVED

        company.activate_network_membership()
        assert company.network_status == NetworkStatus.NETWORK_ACTIVE
        assert company.network_joined_at is not None
        assert company.is_network_eligible_for_jobs is True

    def test_cannot_activate_without_approval(self):
        company = self._company()
        company.apply_to_network()
        with pytest.raises(ValidationError):
            company.activate_network_membership()

    def test_cannot_apply_twice(self):
        company = self._company()
        company.apply_to_network()
        with pytest.raises(ValidationError):
            company.apply_to_network()

    def test_suspending_network_membership_does_not_cancel_subscription(self):
        company = self._company()
        company.apply_to_network()
        company.approve_network_membership()
        company.activate_network_membership()
        assert company.cydrive_subscription_active is True

        company.suspend_network_membership()

        assert company.network_status == NetworkStatus.NETWORK_SUSPENDED
        assert company.cydrive_subscription_active is True  # untouched
        assert company.is_network_eligible_for_jobs is False

    def test_suspended_company_can_still_use_cydrive_standalone(self):
        company = self._company()
        company.apply_to_network()
        company.approve_network_membership()
        company.activate_network_membership()
        company.suspend_network_membership()

        # Subscription independent of network status — company keeps using
        # CyDrive for its own (non-CyMart) deliveries.
        company.refresh_from_db()
        assert company.cydrive_subscription_active is True

    def test_cannot_suspend_a_non_active_membership(self):
        company = self._company()
        with pytest.raises(ValidationError):
            company.suspend_network_membership()
