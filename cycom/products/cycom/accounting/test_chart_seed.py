"""Chart of accounts from the country pack: country-specific accounts,
Arabic names for Arabic tenants, idempotent, never touches existing
accounts, finance role only."""
import uuid

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant
from products.cycom.accounting.models import Account

pytestmark = pytest.mark.django_db


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def make(roles=("tenant_admin",)):
        token = mint_token({"sub": str(uuid.uuid4()), "tenant_id": str(tenant_id),
                            "realm_access": {"roles": list(roles)}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return make


def _seed(c, **body):
    return c.post("/api/v1/accounting/chart/seed/", body, format="json")


def test_saudi_chart_has_zakat_and_end_of_service_in_arabic(client_for, tenant_id):
    Tenant.objects.create(id=tenant_id, name="ksa", slug="ksa", country_code="SA", locale="ar")
    resp = _seed(client_for())
    assert resp.status_code == 200, resp.data
    assert resp.data["created"] == resp.data["total"] == 36
    accounts = {a.code: a for a in Account.objects.filter(tenant_id=tenant_id)}
    assert accounts["2160"].name == "الزكاة المستحقة"
    assert accounts["2210"].parent.code == "2200"
    assert accounts["1000"].is_postable is False          # header with children
    assert accounts["2120"].is_postable is True


def test_uk_chart_in_english_with_paye(client_for, tenant_id):
    Tenant.objects.create(id=tenant_id, name="uk", slug="uk", country_code="GB", locale="en")
    _seed(client_for())
    names = dict(Account.objects.filter(tenant_id=tenant_id).values_list("code", "name"))
    assert names["2160"] == "PAYE & NIC Payable" and names["1130"] == "Accounts Receivable"
    assert "2210" not in names                             # no GCC end-of-service provision


def test_reseeding_fills_gaps_and_never_overwrites(client_for, tenant_id):
    Tenant.objects.create(id=tenant_id, name="jo", slug="jo", country_code="JO", locale="en")
    Account.objects.create(tenant_id=tenant_id, code="1130", name="Customers (my name)", account_type="asset")
    first = _seed(client_for()).data
    assert first["existing"] == 1
    assert Account.objects.get(tenant_id=tenant_id, code="1130").name == "Customers (my name)"
    again = _seed(client_for()).data
    assert again["created"] == 0 and again["existing"] == again["total"]


def test_unknown_country_and_role_guard(client_for, tenant_id):
    Tenant.objects.create(id=tenant_id, name="us", slug="us", country_code="US")
    assert _seed(client_for()).status_code == 400
    assert _seed(client_for(roles=("sales_rep",)), country_code="JO").status_code == 403
