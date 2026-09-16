import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.finance.models import Account


@pytest.fixture
def finance(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "email": "f@cyed.edu.au", "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["finance"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


@pytest.mark.django_db
def test_balanced_entry_posts_and_trial_balance(finance, tenant_id):
    cash = Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset")
    income = Account.objects.create(tenant_id=tenant_id, code="4000", name="Tuition Income", account_type="income")

    ok = finance.post("/api/v1/finance/journal-entries/", {
        "reference": "JE1", "narration": "Tuition received", "date": "2026-02-01",
        "lines": [{"account": str(cash.id), "debit": "1000"}, {"account": str(income.id), "credit": "1000"}],
    }, format="json")
    assert ok.status_code == 201, ok.data
    assert ok.data["is_balanced"] is True

    tb = finance.get("/api/v1/finance/trial-balance/")
    assert tb.status_code == 200
    assert tb.data["balanced"] is True
    assert tb.data["total_debit"] == "1000.00"


@pytest.mark.django_db
def test_unbalanced_entry_rejected(finance, tenant_id):
    a = Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset")
    b = Account.objects.create(tenant_id=tenant_id, code="4000", name="Income", account_type="income")
    resp = finance.post("/api/v1/finance/journal-entries/", {
        "reference": "JE2",
        "lines": [{"account": str(a.id), "debit": "1000"}, {"account": str(b.id), "credit": "900"}],
    }, format="json")
    assert resp.status_code == 400
