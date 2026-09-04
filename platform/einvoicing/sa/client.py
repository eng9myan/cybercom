"""
ZATCA Fatoora API client (Phase 2).

Endpoints used:
  POST /compliance                     — CSID compliance CSR -> binary security token + secret
  POST /compliance/invoices            — compliance check for a generated invoice
  POST /invoices/clearance/single      — standard (B2B) invoice: cleared, then valid to send
  POST /invoices/reporting/single      — simplified (B2C) invoice: reported within 24h

Auth is HTTP Basic with (binary security token, secret) from the CSID step.
Sandbox / simulation / production are switched by base URL.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("platform.einvoicing.sa.client")

ENVS = {
    "sandbox": "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal",
    "simulation": "https://gw-fatoora.zatca.gov.sa/e-invoicing/simulation",
    "production": "https://gw-fatoora.zatca.gov.sa/e-invoicing/core",
}
DEFAULT_TIMEOUT = 30.0


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


class ZatcaClient:
    def __init__(
        self,
        *,
        env: str | None = None,
        csid_token: str | None = None,
        csid_secret: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = ENVS.get((env or _env("ZATCA_ENV", "sandbox")).lower(), ENVS["sandbox"])
        self.csid_token = csid_token or _env("ZATCA_CSID_TOKEN")
        self.csid_secret = csid_secret or _env("ZATCA_CSID_SECRET")
        self.timeout = timeout
        self._injected = client

    def _get_client(self) -> tuple[httpx.Client, bool]:
        if self._injected is not None:
            return self._injected, False
        return httpx.Client(timeout=self.timeout), True

    def _auth_headers(self) -> dict[str, str]:
        token = base64.b64encode(
            f"{self.csid_token}:{self.csid_secret}".encode("utf-8")
        ).decode("ascii")
        return {
            "Authorization": f"Basic {token}",
            "Accept-Version": "V2",
            "Content-Type": "application/json",
            "Accept-Language": "en",
        }

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        client, owned = self._get_client()
        try:
            resp = client.post(
                f"{self.base_url}{path}", json=body, headers=self._auth_headers(),
                timeout=self.timeout,
            )
        finally:
            if owned:
                client.close()
        logger.info("zatca %s http=%s", path, resp.status_code)
        resp.raise_for_status()
        return _safe_json(resp)

    def clear_invoice(self, *, invoice_hash_b64: str, uuid: str, invoice_b64: str) -> dict[str, Any]:
        """Standard (B2B) — /invoices/clearance/single. On success the response
        carries the ZATCA-cleared invoice (with the QR ZATCA issues)."""
        raw = self._post("/invoices/clearance/single", {
            "invoiceHash": invoice_hash_b64, "uuid": uuid, "invoice": invoice_b64,
        })
        return {
            "status": "cleared" if raw.get("clearanceStatus") == "CLEARED" else raw.get("clearanceStatus", "unknown"),
            "reference": raw.get("clearanceStatus", ""),
            "qr": _extract_qr(raw),
            "raw": raw,
        }

    def report_invoice(self, *, invoice_hash_b64: str, uuid: str, invoice_b64: str) -> dict[str, Any]:
        """Simplified (B2C) — /invoices/reporting/single."""
        raw = self._post("/invoices/reporting/single", {
            "invoiceHash": invoice_hash_b64, "uuid": uuid, "invoice": invoice_b64,
        })
        return {
            "status": "reported" if raw.get("reportingStatus") == "REPORTED" else raw.get("reportingStatus", "unknown"),
            "reference": raw.get("reportingStatus", ""),
            "qr": "",
            "raw": raw,
        }

    # unified entry the engine calls
    def submit(self, *, is_simplified: bool, invoice_hash_b64: str, uuid: str, invoice_b64: str) -> dict[str, Any]:
        if is_simplified:
            return self.report_invoice(invoice_hash_b64=invoice_hash_b64, uuid=uuid, invoice_b64=invoice_b64)
        return self.clear_invoice(invoice_hash_b64=invoice_hash_b64, uuid=uuid, invoice_b64=invoice_b64)


def _extract_qr(raw: dict[str, Any]) -> str:
    cleared = raw.get("clearedInvoice") or ""
    if not cleared:
        return ""
    try:
        xml = base64.b64decode(cleared).decode("utf-8", "ignore")
    except Exception:
        return ""
    # QR sits in <cbc:EmbeddedDocumentBinaryObject> under the QR AdditionalDocumentReference
    marker = 'mimeCode="text/plain">'
    if "QR" in xml and marker in xml:
        seg = xml.split(marker)
        for chunk in seg[1:]:
            val = chunk.split("<")[0].strip()
            if len(val) > 40:  # QR payloads are long; PIH seed is 64 chars of zeros
                return val
    return ""


def _safe_json(resp: httpx.Response) -> dict[str, Any]:
    try:
        data = resp.json()
    except ValueError:
        return {"text": resp.text}
    return data if isinstance(data, dict) else {"data": data}


__all__ = ["ZatcaClient"]
