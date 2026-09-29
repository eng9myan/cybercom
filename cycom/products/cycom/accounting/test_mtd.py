"""
UK MTD VAT through CyCom's API with HMRC faked at the client boundary:
boxes from real posted invoices, OAuth state bound to the tenant, tokens
stored encrypted, the legal declaration enforced, one filing per period.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.db import connection
from rest_framework.test import APIClient

from platform.common.tenant_context import tenant_context
from platform.einvoicing.models import HmrcMtdConnection, MtdVatSubmission
from products.cycom.accounting import mtd_views
from products.cycom.accounting.models import Account
from products.cycom.accounting.mtd_views import vrn_valid
from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner

pytestmark = pytest.mark.django_db
VRN = "123456782"
BROWSER = {"device_id": "beec798b-b366-47fa-b1f8-92cede14a1ce", "user_agent": "Mozilla/5.0 (Test)",
           "screens": {"width": 1920, "height": 1080, "scaling_factor": 1, "colour_depth": 24},
           "window_size": {"width": 1256, "height": 803}, "timezone": "UTC+01:00"}


class FakeHmrc:
    configured, sandbox = True, True

    def __init__(self):
        self.submitted = []

    def authorize_url(self, state):
        return f"https://test-api.service.hmrc.gov.uk/oauth/authorize?state={state}"

    def exchange_code(self, code):
        assert code == "good-code"
        return {"access_token": "access-secret", "refresh_token": "refresh-secret", "expires_in": 14400}

    def refresh(self, token):
        return {"access_token": "access-2", "refresh_token": token, "expires_in": 14400}

    def obligations(self, vrn, token, fraud, date_from, date_to):
        assert fraud["Gov-Client-Connection-Method"] == "WEB_APP_VIA_SERVER"
        return [{"periodKey": "26C1", "start": "2026-07-01", "end": "2026-09-30", "status": "O", "due": "2026-11-07"}]

    def submit_return(self, vrn, token, fraud, body):
        assert token == "access-secret"
        self.submitted.append(body)
        return {"processingDate": "2026-10-02T09:00:00.000Z", "formBundleNumber": "256660290587", "receipt_id": "r1"}


@pytest.fixture
def hmrc(monkeypatch):
    fake = FakeHmrc()
    monkeypatch.setattr(mtd_views, "_client", lambda: fake)
    return fake


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def make(roles=("tenant_admin",), tid=None):
        token = mint_token({"sub": str(uuid.uuid4()), "email": "fd@cycom.co.uk", "tenant_id": str(tid or tenant_id),
                            "realm_access": {"roles": list(roles)}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return make


@pytest.fixture
def ledger(tenant_id):
    acc = {k: Account.objects.create(tenant_id=tenant_id, code=c, name=k, account_type=t) for k, c, t in (
        ("ar", "1100", "asset"), ("ap", "2100", "liability"), ("vat", "2200", "liability"),
        ("rev", "4000", "income"), ("exp", "5000", "expense"))}
    cust = Partner.objects.create(tenant_id=tenant_id, name="Customer Ltd", partner_type="customer")
    supp = Partner.objects.create(tenant_id=tenant_id, name="Supplier Ltd", partner_type="vendor")

    def inv(kind, partner, net, pct, when=date(2026, 8, 10), currency="GBP", status="posted"):
        i = Invoice.objects.create(
            tenant_id=tenant_id, invoice_type=kind, number=f"N-{uuid.uuid4().hex[:6]}", partner=partner, date=when,
            due_date=when, currency=currency, status=status,
            control_account=acc["ar"] if "customer" in kind else acc["ap"], tax_account=acc["vat"],
            amount_subtotal=Decimal(net), amount_tax=(Decimal(net) * Decimal(pct) / 100).quantize(Decimal("0.01")))
        InvoiceLine.objects.create(tenant_id=tenant_id, invoice=i, account=acc["rev"], quantity=1,
                                   unit_price=Decimal(net), tax_percent=Decimal(pct))
        return i

    inv("customer", cust, "10000.40", "20")
    inv("customer", cust, "500.00", "5")
    inv("customer_credit_note", cust, "400.00", "20")
    inv("vendor", supp, "3000.00", "20")
    inv("customer", cust, "999.00", "20", when=date(2026, 10, 1))      # outside period
    inv("customer", cust, "777.00", "20", status="draft")               # not posted
    return inv, cust


def _connect(c):
    url = c.post("/api/v1/accounting/mtd/connect/", {"vrn": VRN}, format="json").data["authorize_url"]
    state = url.split("state=")[1]
    return c.post("/api/v1/accounting/mtd/callback/", {"code": "good-code", "state": state}, format="json")


def test_vrn_check_digits():
    assert vrn_valid(VRN)
    assert not vrn_valid("123456789")


def test_preview_boxes_from_posted_invoices(ledger, client_for):
    resp = client_for().get("/api/v1/accounting/mtd/preview/?date_from=2026-07-01&date_to=2026-09-30")
    assert resp.status_code == 200, resp.data
    b = resp.data["boxes"]
    # sales VAT 2000.08 + 25.00 - 80.00 = 1945.08 ; purchases VAT 600.00
    assert (b["box1"], b["box3"], b["box4"], b["box5"]) == ("1945.08", "1945.08", "600.00", "1345.08")
    assert (b["box6"], b["box7"], b["box2"], b["box8"]) == (10100, 3000, "0.00", 0)
    assert resp.data["notes"]


def test_foreign_currency_invoice_is_refused(ledger, client_for):
    inv, cust = ledger
    inv("customer", cust, "100", "20", currency="EUR")
    resp = client_for().get("/api/v1/accounting/mtd/preview/?date_from=2026-07-01&date_to=2026-09-30")
    assert resp.status_code == 400 and resp.data["problems"][0]["key"] == "currency"


def test_connect_stores_tokens_encrypted_and_binds_state_to_the_tenant(ledger, hmrc, client_for, tenant_id):
    c = client_for()
    resp = _connect(c)
    assert resp.status_code == 200 and resp.data["connected"] and resp.data["vrn"] == VRN
    with connection.cursor() as cur:
        cur.execute("SELECT access_token FROM platform_hmrc_mtd_connections")
        raw = bytes(cur.fetchone()[0])
    assert b"access-secret" not in raw                       # encrypted at rest
    assert HmrcMtdConnection.objects.get(tenant_id=tenant_id).access_token != "access-secret"  # masked w/o context
    with tenant_context(tenant_id):
        assert HmrcMtdConnection.objects.get(tenant_id=tenant_id).access_token == "access-secret"

    # a state minted for tenant A can't be redeemed by tenant B
    url = c.post("/api/v1/accounting/mtd/connect/", {"vrn": VRN}, format="json").data["authorize_url"]
    other = client_for(tid=uuid.uuid4())
    bad = other.post("/api/v1/accounting/mtd/callback/", {"code": "good-code", "state": url.split("state=")[1]},
                     format="json")
    assert bad.status_code == 400
    tampered = c.post("/api/v1/accounting/mtd/callback/", {"code": "good-code", "state": "forged"}, format="json")
    assert tampered.status_code == 400


def test_invalid_vrn_and_role_checks(hmrc, client_for):
    assert client_for().post("/api/v1/accounting/mtd/connect/", {"vrn": "123456789"}, format="json").status_code == 400
    assert client_for(roles=("sales_rep",)).post("/api/v1/accounting/mtd/connect/", {"vrn": VRN},
                                                 format="json").status_code == 403


def test_obligations_and_filing(ledger, hmrc, client_for, tenant_id):
    c = client_for()
    _connect(c)
    obs = c.post("/api/v1/accounting/mtd/obligations/", {"browser": BROWSER}, format="json")
    assert obs.status_code == 200 and obs.data[0]["periodKey"] == "26C1" and not obs.data[0]["filed_here"]

    payload = {"period_key": "26C1", "date_from": "2026-07-01", "date_to": "2026-09-30", "browser": BROWSER}
    no_decl = c.post("/api/v1/accounting/mtd/submit/", payload, format="json")
    assert no_decl.status_code == 400 and not hmrc.submitted

    ok = c.post("/api/v1/accounting/mtd/submit/", {**payload, "declaration": True}, format="json")
    assert ok.status_code == 201, ok.data
    assert hmrc.submitted[0]["vatDueSales"] == 1945.08 and hmrc.submitted[0]["totalValueSalesExVAT"] == 10100
    sub = MtdVatSubmission.objects.get(tenant_id=tenant_id)
    assert sub.receipt["formBundleNumber"] == "256660290587" and sub.submitted_by == "fd@cycom.co.uk"

    again = c.post("/api/v1/accounting/mtd/submit/", {**payload, "declaration": True}, format="json")
    assert again.status_code == 409 and len(hmrc.submitted) == 1
    assert c.post("/api/v1/accounting/mtd/obligations/", {"browser": BROWSER}, format="json").data[0]["filed_here"]
    assert len(c.get("/api/v1/accounting/mtd/submissions/").data) == 1


def test_missing_browser_fraud_data_is_refused(ledger, hmrc, client_for):
    c = client_for()
    _connect(c)
    resp = c.post("/api/v1/accounting/mtd/submit/", {"period_key": "26C1", "date_from": "2026-07-01",
                                                     "date_to": "2026-09-30", "declaration": True, "browser": {}},
                  format="json")
    assert resp.status_code == 400 and not hmrc.submitted


def test_unconfigured_hmrc_is_reported_honestly(client_for, monkeypatch):
    for k in ("HMRC_MTD_CLIENT_ID", "HMRC_MTD_CLIENT_SECRET", "HMRC_MTD_REDIRECT_URI"):
        monkeypatch.delenv(k, raising=False)
    resp = client_for().post("/api/v1/accounting/mtd/connect/", {"vrn": VRN}, format="json")
    assert resp.status_code == 503 and resp.data["code"] == "not_configured"
