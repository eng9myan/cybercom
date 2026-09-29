"""
Norwegian SAF-T export end to end: a real customer invoice posted through
the AR/AP API (so the journal entry is the one the ledger really holds),
a payment against it, then the export -- first refused with the complete
to-do list, then produced and validated against Skatteetaten's XSD.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from lxml import etree
from rest_framework.test import APIClient

from platform.einvoicing.models import EInvoiceProfile
from platform.einvoicing.periodic.saft_no import NS, schema_errors
from platform.tenant.models import Tenant, TenantProfile
from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner

pytestmark = pytest.mark.django_db
N = {"n": NS}


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def make(roles=("tenant_admin",), tid=None):
        token = mint_token({"sub": str(uuid.uuid4()), "tenant_id": str(tid or tenant_id),
                            "realm_access": {"roles": list(roles)}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return make


@pytest.fixture
def books(tenant_id):
    t = Tenant.objects.create(id=tenant_id, name="Cycom Norge", slug="cycom-no", country_code="NO")
    TenantProfile.objects.create(tenant=t, legal_name="Cycom Norge AS", vat_number="999999999")
    acc = {
        "ar": Account.objects.create(tenant_id=tenant_id, code="1500", name="Kundefordringer", account_type="asset"),
        "bank": Account.objects.create(tenant_id=tenant_id, code="1920", name="Bank", account_type="asset"),
        "vat": Account.objects.create(tenant_id=tenant_id, code="2700", name="Utgående mva", account_type="liability"),
        "rev": Account.objects.create(tenant_id=tenant_id, code="3000", name="Salgsinntekt", account_type="income"),
    }
    customer = Partner.objects.create(tenant_id=tenant_id, name="Kunde AS", tax_id="922222229",
                                      partner_type="customer")
    return acc, customer


def _post_invoice(c, tenant_id, acc, customer, lines):
    inv = Invoice.objects.create(tenant_id=tenant_id, invoice_type="customer", number=f"INV-{uuid.uuid4().hex[:6]}",
                                 partner=customer, date=date(2026, 3, 5), due_date=date(2026, 3, 19),
                                 currency="NOK", control_account=acc["ar"], tax_account=acc["vat"])
    for desc, price, pct in lines:
        InvoiceLine.objects.create(tenant_id=tenant_id, invoice=inv, account=acc["rev"], description=desc,
                                   quantity=Decimal("1"), unit_price=Decimal(price), tax_percent=Decimal(pct))
    resp = c.post(f"/api/v1/ar-ap/invoices/{inv.pk}/post/", {}, format="json")
    assert resp.status_code == 200, resp.content
    return inv


def _configure(c, acc):
    mapping = {
        str(acc["ar"].id): ("balanseverdiForOmloepsmiddel", "1500"),
        str(acc["bank"].id): ("balanseverdiForOmloepsmiddel", "1920"),
        str(acc["vat"].id): ("kortsiktigGjeld", "2740"),
        str(acc["rev"].id): ("salgsinntekt", "3000"),
    }
    resp = c.patch("/api/v1/accounting/saft/settings/", {
        "accounts": {k: {"grouping_category": v[0], "grouping_code": v[1]} for k, v in mapping.items()},
        "settings": {"saft_contact_first_name": "Ola", "saft_contact_last_name": "Nordmann",
                     "saft_contact_phone": "75757575", "saft_sales_zero_code": "52"},
    }, format="json")
    assert resp.status_code == 200, resp.content


def _export(c):
    return c.get("/api/v1/accounting/saft/export/?date_from=2026-01-01&date_to=2026-12-31")


def test_export_lists_everything_missing_before_producing_anything(books, tenant_id, client_for):
    acc, customer = books
    c = client_for()
    _post_invoice(c, tenant_id, acc, customer, [("Rådgivning", "1000", "25")])
    resp = _export(c)
    assert resp.status_code == 400
    keys = {p["key"] for p in resp.data["problems"]}
    assert {"grouping", "saft_contact_first_name", "saft_contact_phone"} <= keys


def test_mapped_books_export_a_schema_valid_audit_file_with_vat_and_party_balances(books, tenant_id, client_for):
    acc, customer = books
    c = client_for()
    inv = _post_invoice(c, tenant_id, acc, customer, [("Rådgivning", "1000", "25")])
    _configure(c, acc)
    resp = _export(c)
    assert resp.status_code == 200, getattr(resp, "data", resp.content)
    xml = resp.content.decode()
    assert schema_errors(xml) == []
    root = etree.fromstring(resp.content)
    assert root.xpath("string(//n:Company/n:RegistrationNumber)", namespaces=N) == "999999999"
    rev = root.xpath("//n:Line[n:AccountID='3000']", namespaces=N)[0]
    assert rev.xpath("string(n:TaxInformation/n:TaxCode)", namespaces=N) == "3"
    assert rev.xpath("string(n:TaxInformation/n:TaxBase)", namespaces=N) == "1000.00"
    assert rev.xpath("string(n:TaxInformation/n:CreditTaxAmount/n:Amount)", namespaces=N) == "250.00"
    ar_line = root.xpath("//n:Line[n:AccountID='1500']", namespaces=N)[0]
    assert ar_line.xpath("string(n:CustomerID)", namespaces=N) == str(customer.id)[:35]
    cust = root.xpath("//n:Customer", namespaces=N)[0]
    assert cust.xpath("string(n:BalanceAccount/n:ClosingDebitBalance)", namespaces=N) == "1250.00"
    assert root.xpath("string(//n:GeneralLedgerEntries/n:TotalDebit)", namespaces=N) == "1250.00"
    assert root.xpath("string(//n:Transaction/n:TransactionID)", namespaces=N) == inv.number


def test_zero_rated_sale_uses_the_configured_standard_code(books, tenant_id, client_for):
    acc, customer = books
    c = client_for()
    _post_invoice(c, tenant_id, acc, customer, [("Eksport", "500", "0")])
    _configure(c, acc)
    root = etree.fromstring(_export(c).content)
    assert root.xpath("string(//n:Line[n:AccountID='3000']/n:TaxInformation/n:TaxCode)", namespaces=N) == "52"


def test_zero_rated_sale_without_a_default_is_reported(books, tenant_id, client_for):
    acc, customer = books
    c = client_for()
    _post_invoice(c, tenant_id, acc, customer, [("Eksport", "500", "0")])
    _configure(c, acc)
    c.patch("/api/v1/accounting/saft/settings/", {"settings": {"saft_sales_zero_code": ""}}, format="json")
    resp = _export(c)
    assert resp.status_code == 400
    assert any(p["key"] == "tax_code" for p in resp.data["problems"])


def test_settings_reject_unofficial_codes_and_need_a_finance_role(books, client_for):
    acc, _ = books
    bad = client_for().patch("/api/v1/accounting/saft/settings/", {
        "accounts": {str(acc["rev"].id): {"grouping_category": "salgsinntekt", "grouping_code": "9999"}}},
        format="json")
    assert bad.status_code == 400
    denied = client_for(roles=("sales_rep",)).patch("/api/v1/accounting/saft/settings/", {"settings": {}},
                                                    format="json")
    assert denied.status_code == 403


def test_settings_only_touch_the_callers_accounts(books, client_for):
    acc, _ = books
    other = uuid.uuid4()
    resp = client_for(tid=other).patch("/api/v1/accounting/saft/settings/", {
        "accounts": {str(acc["rev"].id): {"grouping_category": "salgsinntekt", "grouping_code": "3000"}}},
        format="json")
    assert resp.status_code == 400
    acc["rev"].refresh_from_db()
    assert "saft" not in (acc["rev"].attributes or {})
