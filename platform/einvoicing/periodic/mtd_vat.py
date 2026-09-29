"""
UK -- Making Tax Digital for VAT: the 9-box VAT return and HMRC's MTD VAT
API (v1.0).

MTD is a periodic VAT *return* submitted over an OAuth2 user-restricted
API, not an invoice format. This module holds the pieces that don't depend
on any product's ledger:

- `NineBoxReturn`: the return, with HMRC's arithmetic and rounding rules
  (boxes 1-5 in pounds and pence, boxes 6-9 in whole pounds, box 3 = 1 + 2,
  box 5 = |3 - 4|) enforced in one place;
- `HmrcMtdClient`: the OAuth2 authorisation-code flow (authorise URL, code
  exchange, refresh) and the obligations / submit-return calls, configured
  by HMRC_MTD_CLIENT_ID / HMRC_MTD_CLIENT_SECRET / HMRC_MTD_REDIRECT_URI
  (HMRC_MTD_API_BASE defaults to HMRC's sandbox). Without credentials it
  raises TransportNotConfigured -- it never pretends a return was filed;
- `fraud_prevention_headers()`: HMRC's mandatory fraud-prevention headers
  for the WEB_APP_VIA_SERVER connection method, built from values the
  user's browser reports plus the server's view of the request. A missing
  mandatory value is an error, not an omitted header.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Any
from urllib.parse import quote, urlencode

import httpx

from ..national.base import TransportNotConfigured

SANDBOX_BASE = "https://test-api.service.hmrc.gov.uk"
ACCEPT = "application/vnd.hmrc.1.0+json"
SCOPES = "read:vat write:vat"
VRN_RE = r"\d{9}"


class HmrcApiError(RuntimeError):
    def __init__(self, status: int, body: Any):
        self.status = status
        self.body = body
        super().__init__(f"HMRC returned {status}: {body}")


@dataclass
class NineBoxReturn:
    vat_due_sales: Decimal                 # box 1
    vat_due_acquisitions: Decimal          # box 2
    vat_reclaimed: Decimal                 # box 4
    total_sales_ex_vat: Decimal            # box 6
    total_purchases_ex_vat: Decimal        # box 7
    total_goods_supplied_ex_vat: Decimal   # box 8
    total_acquisitions_ex_vat: Decimal     # box 9

    @staticmethod
    def _p(v: Decimal) -> Decimal:
        return Decimal(v).quantize(Decimal("0.01"), ROUND_HALF_UP)

    @staticmethod
    def _whole(v: Decimal) -> int:
        # HMRC: boxes 6-9 are whole pounds; pence are dropped, not rounded up
        return int(Decimal(v).quantize(Decimal("1"), ROUND_DOWN))

    @property
    def total_vat_due(self) -> Decimal:            # box 3
        return self._p(self.vat_due_sales) + self._p(self.vat_due_acquisitions)

    @property
    def net_vat_due(self) -> Decimal:              # box 5 (always non-negative)
        return abs(self.total_vat_due - self._p(self.vat_reclaimed))

    @property
    def refund_due(self) -> bool:
        return self._p(self.vat_reclaimed) > self.total_vat_due

    def as_boxes(self) -> dict:
        return {
            "box1": str(self._p(self.vat_due_sales)), "box2": str(self._p(self.vat_due_acquisitions)),
            "box3": str(self.total_vat_due), "box4": str(self._p(self.vat_reclaimed)),
            "box5": str(self.net_vat_due), "box6": self._whole(self.total_sales_ex_vat),
            "box7": self._whole(self.total_purchases_ex_vat),
            "box8": self._whole(self.total_goods_supplied_ex_vat),
            "box9": self._whole(self.total_acquisitions_ex_vat), "refund_due": self.refund_due,
        }

    def to_hmrc(self, period_key: str) -> dict:
        """The exact POST body for /organisations/vat/{vrn}/returns.
        `finalised` is the legal declaration and is only ever sent true
        after the user has confirmed it (the caller enforces that)."""
        return {
            "periodKey": period_key,
            "vatDueSales": float(self._p(self.vat_due_sales)),
            "vatDueAcquisitions": float(self._p(self.vat_due_acquisitions)),
            "totalVatDue": float(self.total_vat_due),
            "vatReclaimedCurrPeriod": float(self._p(self.vat_reclaimed)),
            "netVatDue": float(self.net_vat_due),
            "totalValueSalesExVAT": self._whole(self.total_sales_ex_vat),
            "totalValuePurchasesExVAT": self._whole(self.total_purchases_ex_vat),
            "totalValueGoodsSuppliedExVAT": self._whole(self.total_goods_supplied_ex_vat),
            "totalAcquisitionsExVAT": self._whole(self.total_acquisitions_ex_vat),
            "finalised": True,
        }


# -- fraud prevention -----------------------------------------------------------------
BROWSER_FIELDS = ("device_id", "user_agent", "screens", "window_size", "timezone")


def fraud_prevention_headers(*, browser: dict, client_ip: str, user_id: str,
                             vendor_ip: str = "", client_port: str = "",
                             now: datetime | None = None, version: str = "1.0") -> dict[str, str]:
    """WEB_APP_VIA_SERVER headers. `browser` carries what the page's JS
    reported: device_id (a persistent random id), user_agent
    (navigator.userAgent), screens ({width,height,scaling_factor,colour_depth}),
    window_size ({width,height}), timezone ('UTC+01:00')."""
    missing = [k for k in BROWSER_FIELDS if not browser.get(k)]
    if missing or not client_ip:
        raise ValueError("Missing fraud-prevention data: " + ", ".join(missing + ([] if client_ip else ["client_ip"])))
    if not re.fullmatch(r"UTC[+-]\d{2}:\d{2}", browser["timezone"]):
        raise ValueError("timezone must look like UTC+01:00")
    s, w = browser["screens"], browser["window_size"]
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ts = moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"
    headers = {
        "Gov-Client-Connection-Method": "WEB_APP_VIA_SERVER",
        "Gov-Client-Browser-JS-User-Agent": browser["user_agent"],
        "Gov-Client-Device-ID": browser["device_id"],
        "Gov-Client-Public-IP": client_ip,
        "Gov-Client-Public-IP-Timestamp": ts,
        "Gov-Client-Screens": urlencode({"width": s["width"], "height": s["height"],
                                         "scaling-factor": s.get("scaling_factor", 1),
                                         "colour-depth": s.get("colour_depth", 24)}),
        "Gov-Client-Timezone": browser["timezone"],
        "Gov-Client-User-IDs": urlencode({"cycom": user_id}),
        "Gov-Client-Window-Size": urlencode({"width": w["width"], "height": w["height"]}),
        "Gov-Vendor-Version": urlencode({"CyCom": version}),
        "Gov-Vendor-Product-Name": quote("CyCom ERP"),
    }
    if client_port:
        headers["Gov-Client-Public-Port"] = client_port
    if vendor_ip:
        headers["Gov-Vendor-Public-IP"] = vendor_ip
        headers["Gov-Vendor-Forwarded"] = urlencode({"by": vendor_ip, "for": client_ip})
    return headers


# -- API client ----------------------------------------------------------------------
class HmrcMtdClient:
    def __init__(self, *, timeout: float = 30.0):
        self.base = os.getenv("HMRC_MTD_API_BASE", SANDBOX_BASE).rstrip("/")
        self.client_id = os.getenv("HMRC_MTD_CLIENT_ID", "")
        self.client_secret = os.getenv("HMRC_MTD_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("HMRC_MTD_REDIRECT_URI", "")
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    @property
    def sandbox(self) -> bool:
        return self.base == SANDBOX_BASE

    def _require(self):
        if not self.configured:
            raise TransportNotConfigured(
                "HMRC MTD is not configured. Register the application in HMRC's Developer Hub and set "
                "HMRC_MTD_CLIENT_ID, HMRC_MTD_CLIENT_SECRET and HMRC_MTD_REDIRECT_URI.")

    def authorize_url(self, state: str) -> str:
        self._require()
        return f"{self.base}/oauth/authorize?" + urlencode({
            "response_type": "code", "client_id": self.client_id, "scope": SCOPES,
            "state": state, "redirect_uri": self.redirect_uri})

    def _token(self, data: dict) -> dict:
        self._require()
        resp = httpx.post(f"{self.base}/oauth/token", data={
            **data, "client_id": self.client_id, "client_secret": self.client_secret}, timeout=self.timeout)
        if resp.status_code != 200:
            raise HmrcApiError(resp.status_code, _json(resp))
        return resp.json()

    def exchange_code(self, code: str) -> dict:
        return self._token({"grant_type": "authorization_code", "code": code, "redirect_uri": self.redirect_uri})

    def refresh(self, refresh_token: str) -> dict:
        return self._token({"grant_type": "refresh_token", "refresh_token": refresh_token})

    def _headers(self, token: str, fraud: dict) -> dict:
        return {"Authorization": f"Bearer {token}", "Accept": ACCEPT, **fraud}

    def obligations(self, vrn: str, token: str, fraud: dict, date_from: date, date_to: date) -> list[dict]:
        self._require()
        resp = httpx.get(f"{self.base}/organisations/vat/{vrn}/obligations",
                         params={"from": date_from.isoformat(), "to": date_to.isoformat()},
                         headers=self._headers(token, fraud), timeout=self.timeout)
        if resp.status_code == 404:
            return []
        if resp.status_code != 200:
            raise HmrcApiError(resp.status_code, _json(resp))
        return resp.json().get("obligations", [])

    def submit_return(self, vrn: str, token: str, fraud: dict, body: dict) -> dict:
        self._require()
        resp = httpx.post(f"{self.base}/organisations/vat/{vrn}/returns", json=body,
                          headers={**self._headers(token, fraud), "Content-Type": "application/json"},
                          timeout=self.timeout)
        if resp.status_code != 201:
            raise HmrcApiError(resp.status_code, _json(resp))
        return {
            **resp.json(),
            "receipt_id": resp.headers.get("Receipt-ID", ""),
            "receipt_timestamp": resp.headers.get("Receipt-Timestamp", ""),
            "correlation_id": resp.headers.get("X-CorrelationId", ""),
        }


def _json(resp):
    try:
        return resp.json()
    except ValueError:
        return resp.text[:500]
