"""
Tests for CyMed Commercial — Subscription Platform.
"""
import uuid
from datetime import date
import pytest

from products.cymed.commercial.subscriptions.models import (
    SubscriptionPlan, Subscription, SubscriptionUsage, SubscriptionInvoice, SubscriptionContract
)
from products.cymed.commercial.subscriptions.services import SubscriptionService

TENANT = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
CUSTOMER = uuid.UUID("eeeeeeee-0000-0000-0000-000000000001")


@pytest.fixture
def plan(db):
    return SubscriptionPlan.objects.create(
        tenant_id=TENANT,
        code="cymed_clinic_starter_annual",
        name="CyMed Clinic Starter Annual",
        product_code="cymed_clinic",
        edition_code="starter",
        billing_cycle="annual",
        base_price="5000.00",
        currency="USD",
        per_user_price="50.00",
        per_bed_price="0.00",
        is_active=True,
    )


@pytest.fixture
def monthly_plan(db):
    return SubscriptionPlan.objects.create(
        tenant_id=TENANT,
        code="cymed_clinic_starter_monthly",
        name="CyMed Clinic Starter Monthly",
        product_code="cymed_clinic",
        edition_code="starter",
        billing_cycle="monthly",
        base_price="500.00",
        currency="USD",
    )


@pytest.fixture
def subscription(db, plan):
    return SubscriptionService.create_subscription(
        plan=plan,
        customer_id=CUSTOMER,
        tenant_id=TENANT,
        contracted_users=10,
        contracted_beds=0,
    )


class TestSubscriptionPlan:
    def test_str(self, plan):
        assert "cymed_clinic_starter_annual" in str(plan)

    def test_unique_code(self, db, plan):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            SubscriptionPlan.objects.create(
                tenant_id=TENANT, code="cymed_clinic_starter_annual", name="Dup",
                product_code="x", edition_code="x"
            )


class TestSubscriptionService:
    def test_create_subscription_annual(self, subscription, plan):
        assert subscription.status == "active"
        assert subscription.plan == plan
        assert subscription.contracted_users == 10

    def test_annual_period_end(self, subscription):
        expected_end = date.today().replace(year=date.today().year + 1)
        delta = abs((subscription.current_period_end - expected_end).days)
        assert delta <= 1  # within 1 day

    def test_create_subscription_monthly(self, db, monthly_plan):
        sub = SubscriptionService.create_subscription(
            plan=monthly_plan,
            customer_id=CUSTOMER,
            tenant_id=TENANT,
        )
        from dateutil.relativedelta import relativedelta
        expected = date.today() + relativedelta(months=1) - relativedelta(days=1)
        assert sub.current_period_end == expected

    def test_renew_subscription(self, subscription):
        old_end = subscription.current_period_end
        renewed = SubscriptionService.renew_subscription(subscription)
        assert renewed.current_period_start > old_end

    def test_generate_invoice(self, subscription):
        invoice = SubscriptionService.generate_invoice(subscription)
        assert invoice.status == "draft"
        assert invoice.base_amount > 0
        assert invoice.total_amount == invoice.base_amount + invoice.overage_amount
        assert invoice.currency == "USD"
        assert "INV-" in invoice.invoice_number

    def test_invoice_includes_per_user(self, subscription):
        invoice = SubscriptionService.generate_invoice(subscription)
        # base_price(5000) + per_user(50) * users(10) = 5500
        assert float(invoice.base_amount) == 5500.0


class TestSubscriptionContract:
    def test_create_contract(self, db, subscription):
        contract = SubscriptionContract.objects.create(
            tenant_id=TENANT,
            subscription=subscription,
            contract_number="CONTRACT-2026-001",
            contract_years=3,
            total_contract_value="15000.00",
            sla_tier="gold",
            dedicated_csm=True,
        )
        assert contract.dedicated_csm is True
        assert contract.sla_tier == "gold"
