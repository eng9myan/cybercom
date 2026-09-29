"""UK MTD VAT: 9-box arithmetic, fraud-prevention headers, HMRC client."""
from datetime import date, datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest

from platform.einvoicing.national import TransportNotConfigured
from platform.einvoicing.periodic import mtd_vat
from platform.einvoicing.periodic.mtd_vat import HmrcApiError, HmrcMtdClient, NineBoxReturn, fraud_prevention_headers

BROWSER = {"device_id": "beec798b-b366-47fa-b1f8-92cede14a1ce", "user_agent": "Mozilla/5.0 (Test)",
           "screens": {"width": 1920, "height": 1080, "scaling_factor": 1, "colour_depth": 24},
           "window_size": {"width": 1256, "height": 803}, "timezone": "UTC+01:00"}


def _ret(**kw):
    base = dict(vat_due_sales=Decimal("1000.456"), vat_due_acquisitions=Decimal("0"), vat_reclaimed=Decimal("250.10"),
                total_sales_ex_vat=Decimal("5002.99"), total_purchases_ex_vat=Decimal("1250.50"),
                total_goods_supplied_ex_vat=Decimal("0"), total_acquisitions_ex_vat=Decimal("0"))
    base.update(kw)
    return NineBoxReturn(**base)


def test_box_arithmetic_and_rounding():
    body = _ret().to_hmrc("24A1")
    assert body["vatDueSales"] == 1000.46
    assert body["totalVatDue"] == 1000.46                 # box 3 = 1 + 2
    assert body["netVatDue"] == 750.36                    # box 5 = |3 - 4|
    assert body["totalValueSalesExVAT"] == 5002           # whole pounds, pence dropped
    assert body["totalValuePurchasesExVAT"] == 1250
    assert body["finalised"] is True


def test_refund_position_keeps_box5_positive():
    r = _ret(vat_due_sales=Decimal("100"), vat_reclaimed=Decimal("400"))
    assert r.to_hmrc("24A1")["netVatDue"] == 300.0
    assert r.as_boxes()["refund_due"] is True


def test_fraud_prevention_headers():
    h = fraud_prevention_headers(browser=BROWSER, client_ip="198.51.100.7", user_id="u-1", vendor_ip="203.0.113.5",
                                 client_port="54321", now=datetime(2026, 9, 29, 10, 0, 0, 123000, tzinfo=timezone.utc))
    assert h["Gov-Client-Connection-Method"] == "WEB_APP_VIA_SERVER"
    assert h["Gov-Client-Public-IP-Timestamp"] == "2026-09-29T10:00:00.123Z"
    assert h["Gov-Client-Screens"] == "width=1920&height=1080&scaling-factor=1&colour-depth=24"
    assert h["Gov-Client-Window-Size"] == "width=1256&height=803"
    assert h["Gov-Vendor-Forwarded"] == "by=203.0.113.5&for=198.51.100.7"
    assert h["Gov-Client-User-IDs"] == "cycom=u-1"


def test_fraud_headers_refuse_missing_browser_data():
    with pytest.raises(ValueError):
        fraud_prevention_headers(browser={**BROWSER, "device_id": ""}, client_ip="1.2.3.4", user_id="u")
    with pytest.raises(ValueError):
        fraud_prevention_headers(browser={**BROWSER, "timezone": "Europe/London"}, client_ip="1.2.3.4", user_id="u")


def test_unconfigured_client_refuses(monkeypatch):
    for k in ("HMRC_MTD_CLIENT_ID", "HMRC_MTD_CLIENT_SECRET", "HMRC_MTD_REDIRECT_URI"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(TransportNotConfigured):
        HmrcMtdClient().authorize_url("s")


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("HMRC_MTD_CLIENT_ID", "cid")
    monkeypatch.setenv("HMRC_MTD_CLIENT_SECRET", "secret")
    monkeypatch.setenv("HMRC_MTD_REDIRECT_URI", "https://app.example/accounting/vat-mtd")
    monkeypatch.delenv("HMRC_MTD_API_BASE", raising=False)


class _Resp:
    def __init__(self, status, body, headers=None):
        self.status_code, self._body, self.headers = status, body, headers or {}

    def json(self):
        return self._body


def test_authorize_url_and_code_exchange(configured, monkeypatch):
    c = HmrcMtdClient()
    q = parse_qs(urlparse(c.authorize_url("st8")).query)
    assert q["scope"] == ["read:vat write:vat"] and q["state"] == ["st8"] and c.sandbox
    sent = {}

    def fake_post(url, data=None, **kw):
        sent.update(url=url, data=data)
        return _Resp(200, {"access_token": "a", "refresh_token": "r", "expires_in": 14400})

    monkeypatch.setattr(mtd_vat.httpx, "post", fake_post)
    assert c.exchange_code("abc")["access_token"] == "a"
    assert sent["url"].endswith("/oauth/token") and sent["data"]["grant_type"] == "authorization_code"


def test_submit_return_sends_fraud_headers_and_returns_the_receipt(configured, monkeypatch):
    seen = {}

    def fake_post(url, json=None, headers=None, **kw):
        seen.update(url=url, json=json, headers=headers)
        return _Resp(201, {"processingDate": "2026-09-29T10:00:00.000Z", "formBundleNumber": "256660290587"},
                     {"Receipt-ID": "rid-1", "X-CorrelationId": "cid-1"})

    monkeypatch.setattr(mtd_vat.httpx, "post", fake_post)
    fraud = fraud_prevention_headers(browser=BROWSER, client_ip="198.51.100.7", user_id="u")
    receipt = HmrcMtdClient().submit_return("123456782", "tok", fraud, _ret().to_hmrc("24A1"))
    assert seen["url"].endswith("/organisations/vat/123456782/returns")
    assert seen["headers"]["Accept"] == "application/vnd.hmrc.1.0+json"
    assert seen["headers"]["Gov-Client-Connection-Method"] == "WEB_APP_VIA_SERVER"
    assert receipt["formBundleNumber"] == "256660290587" and receipt["receipt_id"] == "rid-1"


def test_hmrc_error_surfaces(configured, monkeypatch):
    monkeypatch.setattr(mtd_vat.httpx, "post",
                        lambda *a, **k: _Resp(403, {"code": "DUPLICATE_SUBMISSION"}))
    with pytest.raises(HmrcApiError) as exc:
        HmrcMtdClient().submit_return("123456782", "t", {}, {})
    assert exc.value.status == 403


def test_obligations_404_means_none(configured, monkeypatch):
    monkeypatch.setattr(mtd_vat.httpx, "get", lambda *a, **k: _Resp(404, {"code": "NOT_FOUND"}))
    assert HmrcMtdClient().obligations("123456782", "t", {}, date(2026, 1, 1), date(2026, 12, 31)) == []
