"""
National-format e-invoicing through the real Invoice bridge + API, using
Italy (FatturaPA) as the exemplar: every national format shares this path.

Covers the honest-failure contract end to end: an invoice missing national
data comes back `incomplete` with the exact fields to fill (and burns no
sequence number); once filled, with no SdI channel configured, the legal
document is `generated`, stored and downloadable; configuring a transport
later transmits that same stored document rather than rebuilding it.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from platform.einvoicing.models import EInvoiceInteraction, EInvoiceProfile, EInvoiceSequence
from platform.einvoicing.national.it_fatturapa import ItFatturaPA
from platform.tenant.models import Tenant, TenantProfile
from products.cycom.accounting.models import Account
from products.cycom.ar_ap import einvoice as bridge
from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner

pytestmark = pytest.mark.django_db


@pytest.fixture
def it_tenant(tenant_id):
    t = Tenant.objects.create(id=tenant_id, name="Cycom Italia", slug="cycom-italia", country_code="IT")
    TenantProfile.objects.create(tenant=t, legal_name="Cycom Italia S.r.l.", vat_number="01234567890")
    return t


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def make(roles=("tenant_admin",)):
        token = mint_token({
            "sub": str(uuid.uuid4()), "email": "fin@cycom.it", "tenant_id": str(tenant_id),
            "realm_access": {"roles": list(roles)},
        })
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return make


@pytest.fixture
def invoice(it_tenant, tenant_id):
    ar = Account.objects.create(tenant_id=tenant_id, code="1100", name="AR", account_type="asset")
    rev = Account.objects.create(tenant_id=tenant_id, code="4000", name="Rev", account_type="income")
    vat = Account.objects.create(tenant_id=tenant_id, code="2120", name="IVA", account_type="liability")
    partner = Partner.objects.create(tenant_id=tenant_id, name="Cliente S.p.A.", tax_id="IT09876543210",
                                     city="Torino")
    inv = Invoice.objects.create(
        tenant_id=tenant_id, invoice_type="customer", number="FT-2026-0001", partner=partner,
        date=date(2026, 9, 1), due_date=date(2026, 10, 1), currency="EUR",
        control_account=ar, tax_account=vat, status="posted",
    )
    InvoiceLine.objects.create(tenant_id=tenant_id, invoice=inv, account=rev, description="Consulenza",
                               quantity=Decimal("10"), unit_price=Decimal("100"), tax_percent=Decimal("22"))
    InvoiceLine.objects.create(tenant_id=tenant_id, invoice=inv, account=rev, description="Export",
                               quantity=Decimal("1"), unit_price=Decimal("50"), tax_percent=Decimal("0"))
    return inv


def _fill(tenant_id, inv):
    EInvoiceProfile.objects.create(
        tenant_id=tenant_id, street="Via Roma", building_number="10", city="Milano",
        postal_code="20121", region="MI", national={"regime_fiscale": "RF01", "default_natura": "N3.1"},
    )
    p = inv.partner
    p.attributes = {"einvoice": {"street": "Corso Italia 5", "postal_code": "10121", "country_code": "IT",
                                 "codice_destinatario": "ABC1234"}}
    p.save()


def test_incomplete_invoice_lists_missing_fields_and_burns_no_sequence(invoice, tenant_id):
    bridge.run_einvoice_clearance(invoice)
    invoice.refresh_from_db()
    assert invoice.einvoice_mode == "it_fatturapa"
    assert invoice.einvoice_status == "incomplete"
    keys = {(p["scope"], p["key"]) for p in invoice.einvoice_response["problems"]}
    assert ("seller", "regime_fiscale") in keys
    # buyer country unknown -> asked for; the SdI code is only required
    # once the buyer is known to be Italian (foreign buyers get XXXXXXX)
    assert ("buyer", "country_code") in keys
    assert any(k[1] == "natura" for k in keys)  # the 0% line
    assert not EInvoiceSequence.objects.filter(tenant_id=tenant_id).exists()
    assert not EInvoiceInteraction.objects.filter(tenant_id=tenant_id).exists()


def test_complete_invoice_without_transport_is_generated_stored_and_schema_valid(invoice, tenant_id, monkeypatch):
    monkeypatch.delenv("SDI_BASE_URL", raising=False)
    _fill(tenant_id, invoice)
    bridge.run_einvoice_clearance(invoice)
    invoice.refresh_from_db()
    assert invoice.einvoice_status == "generated", invoice.einvoice_response
    assert "SDI_BASE_URL" in invoice.einvoice_response["error"]
    interaction = EInvoiceInteraction.objects.get(tenant_id=tenant_id)
    assert interaction.document_filename == "IT01234567890_00001.xml"
    assert ItFatturaPA().schema_errors(interaction.document) == []
    assert EInvoiceSequence.objects.get(tenant_id=tenant_id).next_icv == 2  # issued -> advances


def test_generated_document_is_resubmitted_as_is_once_transport_exists(invoice, tenant_id, monkeypatch):
    monkeypatch.delenv("SDI_BASE_URL", raising=False)
    _fill(tenant_id, invoice)
    bridge.run_einvoice_clearance(invoice)
    stored = EInvoiceInteraction.objects.get(tenant_id=tenant_id).document

    sent = {}

    class _FakeSdi:
        configured = True

        def submit(self, document, *, filename, doc=None):
            sent["document"], sent["filename"] = document, filename
            return {"status": "submitted", "reference": "SDI-778", "raw": {}}

    monkeypatch.setattr(ItFatturaPA, "client", lambda self: _FakeSdi())
    invoice.refresh_from_db()
    bridge.resubmit_generated(invoice)
    invoice.refresh_from_db()
    assert invoice.einvoice_status == "cleared"
    assert invoice.einvoice_reference == "SDI-778"
    assert sent["document"] == stored               # not rebuilt
    assert sent["filename"] == "IT01234567890_00001.xml"
    assert EInvoiceInteraction.objects.filter(tenant_id=tenant_id).count() == 1


def test_profile_api_exposes_the_formats_seller_fields_and_validates(it_tenant, client_for):
    c = client_for()
    resp = c.get("/api/v1/ar-ap/einvoice-profile/")
    assert resp.status_code == 200
    assert resp.data["mode"] == "it_fatturapa"
    assert "regime_fiscale" in {f["key"] for f in resp.data["fields"]}
    assert resp.data["fallbacks"]["tax_id"] == "01234567890"

    bad = c.put("/api/v1/ar-ap/einvoice-profile/", {"values": {"postal_code": "ABC"}}, format="json")
    assert bad.status_code == 400
    ok = c.put("/api/v1/ar-ap/einvoice-profile/",
               {"values": {"postal_code": "20121", "regime_fiscale": "RF01", "name": "Cycom Italia S.r.l."}},
               format="json")
    assert ok.status_code == 200
    ep = EInvoiceProfile.objects.get(tenant_id=it_tenant.id)
    assert ep.postal_code == "20121" and ep.national == {"regime_fiscale": "RF01"}
    assert ep.legal_name == "Cycom Italia S.r.l."


def test_profile_write_requires_a_finance_role(it_tenant, client_for):
    resp = client_for(roles=("sales_rep",)).put(
        "/api/v1/ar-ap/einvoice-profile/", {"values": {"postal_code": "20121"}}, format="json")
    assert resp.status_code == 403


def test_fix_then_retry_through_the_api_and_download(invoice, tenant_id, client_for, monkeypatch):
    monkeypatch.delenv("SDI_BASE_URL", raising=False)
    c = client_for()
    bridge.run_einvoice_clearance(invoice)
    state = c.get(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/").data
    assert state["status"] == "incomplete"
    zero_line = next(l for l in state["lines"] if l["tax_percent"].startswith("0"))

    EInvoiceProfile.objects.create(tenant_id=tenant_id, street="Via Roma", city="Milano",
                                   postal_code="20121", national={"regime_fiscale": "RF01"})
    resp = c.patch(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/", {
        "buyer": {"street": "Corso Italia 5", "postal_code": "10121", "country_code": "IT",
                  "codice_destinatario": "ABC1234"},
        "lines": {zero_line["id"]: {"natura": "N3.1"}},
    }, format="json")
    assert resp.status_code == 200, resp.content

    resp = c.post(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/retry/")
    assert resp.status_code == 200, resp.content
    assert resp.data["status"] == "generated"
    assert resp.data["has_document"] is True

    dl = c.get(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/document/")
    assert dl.status_code == 200
    assert "IT01234567890_00001.xml" in dl["Content-Disposition"]
    assert b"<CodiceDestinatario>ABC1234</CodiceDestinatario>" in dl.content

    # issued -> national data is locked
    locked = c.patch(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/", {"buyer": {"pec": "a@b.it"}}, format="json")
    assert locked.status_code == 400


def test_patch_rejects_malformed_values_and_foreign_lines_all_or_nothing(invoice, client_for):
    c = client_for()
    resp = c.patch(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/", {
        "buyer": {"street": "Via Nuova 1"},                     # valid on its own
        "document": {},
        "lines": {str(uuid.uuid4()): {"natura": "N3.1"}, "not-a-uuid": {"natura": "N4"}},
    }, format="json")
    assert resp.status_code == 400
    assert len(resp.data["errors"]) == 2
    invoice.partner.refresh_from_db()
    assert "einvoice" not in (invoice.partner.attributes or {})  # rolled back

    resp = c.patch(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/",
                   {"buyer": {"codice_destinatario": "lower!"}}, format="json")
    assert resp.status_code == 400 and resp.data["errors"][0]["key"] == "codice_destinatario"


def test_einvoice_endpoints_are_tenant_isolated(invoice, client_for, mint_token, mock_jwks):
    token = mint_token({"sub": str(uuid.uuid4()), "tenant_id": str(uuid.uuid4()),
                        "realm_access": {"roles": ["tenant_admin"]}})
    other = APIClient()
    other.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert other.get(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/").status_code == 404
    assert other.get(f"/api/v1/ar-ap/invoices/{invoice.pk}/einvoice/document/").status_code == 404
