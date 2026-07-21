"""
CyID ecosystem, Phase 8 — cross-network cart/checkout: one wallet debit
paying for a real cymed order + a real (mocked-HTTP) cyshop order,
verified end-to-end through the actual API, not the service layer
directly.
"""

import uuid
from datetime import date
from unittest.mock import Mock, patch

import pytest
from rest_framework.test import APIClient

from platform.cyidentity.models import IdentityRealm, PersonIdentity, RealmStatus, RealmType
from platform.wallet.models import CheckoutReceipt, WalletAccount
from platform.wallet.services import WalletService
from products.cymed.core.orders.models import Order
from products.cymed.core.patients.models import Patient


@pytest.fixture
def home_realm(db):
    return IdentityRealm.objects.create(
        tenant_id=uuid.uuid4(),
        realm_name="cyid",
        realm_type=RealmType.CITIZEN,
        status=RealmStatus.ACTIVE,
        issuer_url="http://x/realms/cyid",
        jwks_uri="http://x/realms/cyid/jwks",
        admin_api_url="http://x/admin/realms/cyid",
    )


@pytest.fixture
def person(home_realm):
    return PersonIdentity.objects.create(
        home_realm=home_realm, display_name="Jane Patient", primary_email="jane@example.com"
    )


def _admin_client(mint_token, mock_jwks):
    client = APIClient()
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(uuid.uuid4()),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _make_pharmacy_order(tenant_id):
    patient = Patient.objects.create(
        tenant_id=tenant_id,
        first_name="Jane",
        last_name="Patient",
        dob="1990-01-01",
        gender="female",
        mrn=f"MRN-{uuid.uuid4().hex[:10].upper()}",
    )
    return Order.objects.create(
        tenant_id=tenant_id,
        patient=patient,
        order_type="medication",
        ordered_by="Dr. Noor",
        fulfilling_tenant_id=uuid.uuid4(),  # a pharmacy tenant
    )


@pytest.mark.django_db
class TestCrossNetworkCheckout:
    def test_cymed_only_checkout_debits_wallet_and_records_receipt(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        WalletService().top_up(person, "USD", 100)
        order = _make_pharmacy_order(uuid.uuid4())

        resp = admin.post(
            "/api/v1/commerce/checkout/",
            {
                "person_id": str(person.id),
                "currency": "USD",
                "cymed_items": [{"order_id": str(order.id), "amount": "25.00", "description": "pharmacy copay"}],
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["total_amount"] == "25.00"
        assert len(resp.data["lines"]) == 1
        assert resp.data["lines"][0]["item_type"] == "cymed_order"

        wallet = WalletAccount.objects.get(person=person, currency="USD")
        assert wallet.balance == 75

    def test_mixed_cart_pays_cymed_order_and_places_cyshop_order(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        WalletService().top_up(person, "USD", 200)
        order = _make_pharmacy_order(uuid.uuid4())
        cyshop_tenant = uuid.uuid4()
        company_id = uuid.uuid4()
        branch_id = uuid.uuid4()

        with patch("products.cymed.core.commerce.cyshop_client.httpx.post") as mock_post:
            mock_post.side_effect = [
                Mock(status_code=200, json=lambda: {
                    "access_token": "fake-cyshop-session-token", "user_id": str(uuid.uuid4()),
                }),
                Mock(status_code=201, json=lambda: {"id": str(uuid.uuid4()), "order_number": "CYID-1"}),
            ]
            resp = admin.post(
                "/api/v1/commerce/checkout/",
                {
                    "person_id": str(person.id),
                    "currency": "USD",
                    "cymed_items": [{"order_id": str(order.id), "amount": "25.00"}],
                    "cyshop_items": [
                        {
                            "cyshop_tenant_id": str(cyshop_tenant),
                            "company_id": str(company_id),
                            "branch_id": str(branch_id),
                            "item_name": "Wound care kit",
                            "qty": "1",
                            "unit_price": "40.00",
                        }
                    ],
                    "cyid_token": "real-cyid-token-would-go-here",
                    "customer_name": "Jane Patient",
                },
                format="json",
            )
        assert resp.status_code == 201, resp.content
        assert resp.data["total_amount"] == "65.00"
        assert len(resp.data["lines"]) == 2
        line_types = {line["item_type"] for line in resp.data["lines"]}
        assert line_types == {"cymed_order", "cyshop_order"}

        wallet = WalletAccount.objects.get(person=person, currency="USD")
        assert wallet.balance == 135

        # Real call chain confirmed: exchange first, order placement second.
        assert mock_post.call_count == 2
        exchange_call, order_call = mock_post.call_args_list
        assert exchange_call[0][0].endswith("/cyid-exchange/")
        assert order_call[0][0].endswith("/sales/orders/")
        assert order_call[1]["headers"]["Authorization"] == "Bearer fake-cyshop-session-token"

    def test_insufficient_funds_rejected_no_side_effects(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        WalletService().top_up(person, "USD", 5)
        order = _make_pharmacy_order(uuid.uuid4())

        resp = admin.post(
            "/api/v1/commerce/checkout/",
            {
                "person_id": str(person.id),
                "currency": "USD",
                "cymed_items": [{"order_id": str(order.id), "amount": "999.00"}],
            },
            format="json",
        )
        assert resp.status_code == 402
        wallet = WalletAccount.objects.get(person=person, currency="USD")
        assert wallet.balance == 5
        assert not CheckoutReceipt.objects.filter(person=person).exists()

    def test_unknown_order_rejected_before_any_charge(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        WalletService().top_up(person, "USD", 100)

        resp = admin.post(
            "/api/v1/commerce/checkout/",
            {
                "person_id": str(person.id),
                "currency": "USD",
                "cymed_items": [{"order_id": str(uuid.uuid4()), "amount": "10.00"}],
            },
            format="json",
        )
        assert resp.status_code == 400
        wallet = WalletAccount.objects.get(person=person, currency="USD")
        assert wallet.balance == 100  # untouched — validated before the debit

    def test_cyshop_failure_rolls_back_the_whole_checkout(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        WalletService().top_up(person, "USD", 100)

        with patch("products.cymed.core.commerce.cyshop_client.httpx.post") as mock_post:
            mock_post.return_value = Mock(status_code=502, text="cyshop is down")
            resp = admin.post(
                "/api/v1/commerce/checkout/",
                {
                    "person_id": str(person.id),
                    "currency": "USD",
                    "cyshop_items": [
                        {
                            "cyshop_tenant_id": str(uuid.uuid4()),
                            "company_id": str(uuid.uuid4()),
                            "branch_id": str(uuid.uuid4()),
                            "item_name": "Bandages",
                            "qty": "1",
                            "unit_price": "10.00",
                        }
                    ],
                    "cyid_token": "tok",
                },
                format="json",
            )
        assert resp.status_code == 400, resp.content
        # Atomic — the wallet debit rolled back with everything else.
        wallet = WalletAccount.objects.get(person=person, currency="USD")
        assert wallet.balance == 100
        assert not CheckoutReceipt.objects.filter(person=person).exists()
