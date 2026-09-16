"""
CyCom ERP integration client. CyED does NOT re-implement HR / payroll / inventory
/ procurement / fleet / finance — those already exist in CyCom. This client calls
CyCom's API (same shared platform identity + tenant), so a school runs CyCom for
the generic ERP and CyED for the education domain as one ecosystem.

Configured with CYED_CYCOM_URL (CyCom's base URL). The caller's bearer token and
tenant are forwarded, so CyCom applies its own RBAC/tenant isolation.
"""

import json
import os
import urllib.request

# Only these CyCom resources may be proxied (generic ERP surface).
ALLOWED_PREFIXES = (
    "hr/", "payroll/", "leave/", "inventory/", "procurement/", "fleet/",
    "accounting/", "ar-ap/", "maintenance/", "helpdesk/", "documents/", "expenses/",
)


class CycomNotConfigured(Exception):
    pass


class CycomError(Exception):
    def __init__(self, status, detail):
        self.status = status
        self.detail = detail
        super().__init__(detail)


def base_url() -> str:
    url = os.environ.get("CYED_CYCOM_URL", "")
    if not url:
        raise CycomNotConfigured("CyCom ERP is not configured (set CYED_CYCOM_URL).")
    return url.rstrip("/")


def is_allowed(path: str) -> bool:
    return any(path.lstrip("/").startswith(p) for p in ALLOWED_PREFIXES)


def fetch(path, *, token="", tenant_id="", method="GET", body=None, timeout=15):
    url = f"{base_url()}/api/v1/{path.lstrip('/')}"
    headers = {"content-type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if tenant_id:
        headers["X-Tenant-ID"] = str(tenant_id)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"detail": raw}
        raise CycomError(e.code, payload)
