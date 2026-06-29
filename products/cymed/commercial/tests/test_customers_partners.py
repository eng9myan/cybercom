"""
Tests for CyMed Commercial — Customer and Partner Management.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest

from products.cymed.commercial.customer_management.models import (
    Customer,
    CustomerContract,
    CustomerDeployment,
    CustomerOrganization,
    CustomerSuccessPlan,
)
from products.cymed.commercial.partner_management.models import (
    DistributorAgreement,
    Partner,
    PartnerType,
    ResellerAgreement,
)

TENANT = uuid.UUID("00000001-0000-0000-0000-000000000001")


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        tenant_id=TENANT,
        customer_number="CUST-JO-001",
        name="King Hussein Hospital",
        customer_type="hospital",
        country_code="JO",
        status="active",
    )


@pytest.fixture
def partner_type(db):
    return PartnerType.objects.create(
        tenant_id=TENANT,
        code="reseller",
        name="Reseller",
        commission_rate_pct=Decimal("15.00"),
    )


@pytest.fixture
def partner(db, partner_type):
    return Partner.objects.create(
        tenant_id=TENANT,
        partner_number="PART-JO-001",
        name="MedTech Jordan",
        partner_type=partner_type,
        country_code="JO",
        regions_covered=["JO", "IQ"],
        status="active",
        partner_level="gold",
    )


class TestCustomerModel:
    def test_str(self, customer):
        assert "CUST-JO-001" in str(customer)
        assert "King Hussein Hospital" in str(customer)

    def test_unique_customer_number(self, db, customer):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Customer.objects.create(
                tenant_id=TENANT,
                customer_number="CUST-JO-001",
                name="Duplicate",
                customer_type="clinic",
                country_code="JO",
            )


class TestCustomerOrganization:
    def test_create(self, db, customer):
        org = CustomerOrganization.objects.create(
            tenant_id=TENANT,
            customer=customer,
            organization_name="KHH - Main Campus",
            organization_code="KHH-MAIN",
            primary_contact_email="admin@khh.jo",
        )
        assert org.customer == customer


class TestCustomerContract:
    def test_create_contract(self, db, customer):
        contract = CustomerContract.objects.create(
            tenant_id=TENANT,
            customer=customer,
            contract_number="CONTRACT-JO-2026-001",
            contract_type="enterprise",
            status="signed",
            start_date=date(2026, 1, 1),
            end_date=date(2028, 12, 31),
            total_value=Decimal("150000.00"),
            currency="USD",
        )
        assert contract.status == "signed"
        assert contract.total_value == Decimal("150000.00")


class TestCustomerDeployment:
    def test_create_deployment(self, db, customer):
        deploy = CustomerDeployment.objects.create(
            tenant_id=TENANT,
            customer=customer,
            deployment_profile_code="air_gapped",
            product_code="cymed_hospital",
            edition_code="enterprise",
            environment="production",
            is_active=True,
        )
        assert deploy.deployment_profile_code == "air_gapped"


class TestCustomerSuccessPlan:
    def test_health_score(self, db, customer):
        plan = CustomerSuccessPlan.objects.create(
            tenant_id=TENANT,
            customer=customer,
            plan_name="KHH Success Plan 2026",
            health_score=92,
            adoption_percentage=Decimal("78.5"),
            renewal_risk="low",
        )
        assert plan.health_score == 92
        assert plan.renewal_risk == "low"


class TestPartnerModel:
    def test_str(self, partner):
        assert "PART-JO-001" in str(partner)
        assert "MedTech Jordan" in str(partner)

    def test_regions_covered(self, partner):
        assert "JO" in partner.regions_covered
        assert "IQ" in partner.regions_covered


class TestResellerAgreement:
    def test_create_reseller_agreement(self, db, partner):
        agreement = ResellerAgreement.objects.create(
            tenant_id=TENANT,
            partner=partner,
            agreement_number="RA-JO-2026-001",
            territory=["JO"],
            products_authorized=["cymed_clinic", "cymed_hospital"],
            discount_rate_pct=Decimal("20.00"),
            payment_terms_days=30,
            can_white_label=True,
        )
        assert agreement.can_white_label is True
        assert "cymed_clinic" in agreement.products_authorized


class TestDistributorAgreement:
    def test_create_distributor_agreement(self, db, partner):
        agreement = DistributorAgreement.objects.create(
            tenant_id=TENANT,
            partner=partner,
            agreement_number="DA-MENA-2026-001",
            exclusive_territory=["SA"],
            sub_reseller_rights=True,
            localization_rights=True,
            government_bid_rights=True,
            annual_volume_commitment=Decimal("500000.00"),
        )
        assert agreement.government_bid_rights is True
        assert "SA" in agreement.exclusive_territory
