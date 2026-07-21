"""
CyID ecosystem, Phase 7 — real wallet top-up/debit/balance, atomic and
overdraft-safe. Verified via the real API (not the service layer
directly) so auth/permission resolution (platform_admin acting on
another person vs a person acting on themselves) is exercised too.
"""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from platform.cyidentity.models import IdentityRealm, PersonIdentity, RealmStatus, RealmType
from platform.wallet.models import WalletAccount


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
        home_realm=home_realm, display_name="Jane", primary_email="jane@example.com"
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


def _self_client(person, mint_token, mock_jwks):
    client = APIClient()
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": person.primary_email,
            "person_id": str(person.id),
            "realm_access": {"roles": []},
        }
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestWalletAPI:
    def test_admin_topup_then_balance_query(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)

        resp = admin.post(
            "/api/v1/wallet/topup/",
            {"person_id": str(person.id), "currency": "USD", "amount": "100.00", "reference": "seed"},
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["balance_after"] == "100.00"

        resp = admin.get(f"/api/v1/wallet/balance/?person_id={person.id}&currency=USD")
        assert resp.status_code == 200, resp.content
        assert resp.data["balance"] == "100.00"

        wallet = WalletAccount.objects.get(person=person, currency="USD")
        assert wallet.balance == Decimal("100.00")

    def test_debit_reduces_balance_atomically(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        admin.post(
            "/api/v1/wallet/topup/",
            {"person_id": str(person.id), "currency": "USD", "amount": "50.00"},
            format="json",
        )
        resp = admin.post(
            "/api/v1/wallet/debit/",
            {"person_id": str(person.id), "currency": "USD", "amount": "30.00", "reference": "order-1"},
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["balance_after"] == "20.00"

    def test_overdraft_rejected(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        admin.post(
            "/api/v1/wallet/topup/",
            {"person_id": str(person.id), "currency": "USD", "amount": "10.00"},
            format="json",
        )
        resp = admin.post(
            "/api/v1/wallet/debit/",
            {"person_id": str(person.id), "currency": "USD", "amount": "999.00"},
            format="json",
        )
        assert resp.status_code == 402
        wallet = WalletAccount.objects.get(person=person, currency="USD")
        assert wallet.balance == Decimal("10.00")  # unchanged — rejected before mutation

    def test_debit_with_no_wallet_rejected(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        resp = admin.post(
            "/api/v1/wallet/debit/",
            {"person_id": str(person.id), "currency": "EUR", "amount": "5.00"},
            format="json",
        )
        assert resp.status_code == 402

    def test_person_can_check_their_own_balance_via_token_claim(self, person, mint_token, mock_jwks):
        admin = _admin_client(mint_token, mock_jwks)
        admin.post(
            "/api/v1/wallet/topup/",
            {"person_id": str(person.id), "currency": "JOD", "amount": "75.00"},
            format="json",
        )
        self_client = _self_client(person, mint_token, mock_jwks)
        resp = self_client.get("/api/v1/wallet/balance/?currency=JOD")
        assert resp.status_code == 200, resp.content
        assert resp.data["balance"] == "75.00"

    def test_non_admin_cannot_act_on_another_persons_wallet(self, person, mint_token, mock_jwks):
        other_person = PersonIdentity.objects.create(
            home_realm=person.home_realm, display_name="Sam", primary_email="sam@example.com"
        )
        self_client = _self_client(person, mint_token, mock_jwks)
        resp = self_client.post(
            "/api/v1/wallet/topup/",
            {"person_id": str(other_person.id), "currency": "USD", "amount": "1000.00"},
            format="json",
        )
        # Non-admin caller's person_id in the body is ignored — falls back
        # to their own token claim, so this tops up THEIR OWN wallet, not
        # other_person's. Confirmed by other_person having no wallet after.
        assert resp.status_code == 201, resp.content
        assert not WalletAccount.objects.filter(person=other_person, currency="USD").exists()
        assert WalletAccount.objects.filter(person=person, currency="USD").exists()
