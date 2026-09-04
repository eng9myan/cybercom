"""
JoFotara (Jordan ISTD) e-invoicing transport client.

Platform-owned copy of the hardened client (the CyMed
`products.cymed.integrations.jofawtra.client` module will re-export from here
during the CyMed re-home, blueprint D.3 M4). Pure `httpx` — no product deps.

Transport only: submit signed UBL 2.1, poll status. UBL generation is
`platform.einvoicing.ubl`; signing is `platform.einvoicing.signing`;
orchestration is `platform.einvoicing.engine`.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("platform.einvoicing.jofotara")

DEFAULT_BASE_URL = "https://sandbox.jofotara.gov.jo"
DEFAULT_TIMEOUT = 30.0


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


class JoFotaraClient:
    SUBMIT_PATH = "/invoicing/submit"
    STATUS_PATH = "/invoicing/status/{reference}"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        tax_id: str | None = None,
        activity_code: str | None = None,
        auth_kind: str | None = None,
        private_key_path: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or _env("JOFOTARA_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.client_id = client_id or _env("JOFOTARA_CLIENT_ID")
        self.client_secret = client_secret or _env("JOFOTARA_CLIENT_SECRET")
        self.tax_id = tax_id or _env("JOFOTARA_TAX_ID")
        self.activity_code = activity_code or _env("JOFOTARA_ACTIVITY_CODE")
        self.auth_kind = (auth_kind or _env("JOFOTARA_AUTH_KIND", "basic")).lower()
        self.private_key_path = private_key_path or _env("JOFOTARA_PRIVATE_KEY_PATH")
        self.timeout = timeout
        self._injected_client = client

    def _basic_auth_header(self) -> str:
        token = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        ).decode("ascii")
        return f"Basic {token}"

    def _bearer_token(self, client: httpx.Client) -> str:
        resp = client.post(
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token", "")
        if not token:
            raise RuntimeError("JoFotara returned an empty access_token")
        return token

    def _auth_header(self, client: httpx.Client) -> str:
        if self.auth_kind == "bearer":
            return f"Bearer {self._bearer_token(client)}"
        return self._basic_auth_header()

    def _headers(self, client: httpx.Client, *, content_type: str) -> dict[str, str]:
        headers = {
            "Content-Type": content_type,
            "Accept": "application/json",
            "Authorization": self._auth_header(client),
        }
        if self.tax_id:
            headers["Client-Id"] = self.tax_id
        if self.activity_code:
            headers["Activity-Code"] = self.activity_code
        return headers

    def _get_client(self) -> tuple[httpx.Client, bool]:
        if self._injected_client is not None:
            return self._injected_client, False
        return httpx.Client(timeout=self.timeout), True

    def submit_invoice(self, ubl_xml: str, invoice_uuid: str) -> dict[str, Any]:
        if not isinstance(ubl_xml, str) or not ubl_xml.strip():
            raise ValueError("ubl_xml must be a non-empty XML string")
        if not invoice_uuid:
            raise ValueError("invoice_uuid is required")

        payload = base64.b64encode(ubl_xml.encode("utf-8")).decode("ascii")
        body = {"invoice": payload, "invoiceUuid": invoice_uuid, "customizationId": "PINT-JO"}

        client, owned = self._get_client()
        try:
            resp = client.post(
                f"{self.base_url}{self.SUBMIT_PATH}",
                json=body,
                headers=self._headers(client, content_type="application/json"),
                timeout=self.timeout,
            )
        finally:
            if owned:
                client.close()

        logger.info("jofotara.submit uuid=%s http=%s", invoice_uuid, resp.status_code)
        resp.raise_for_status()
        raw = _safe_json(resp)
        return {
            "status": raw.get("status") or ("submitted" if resp.is_success else "error"),
            "reference": raw.get("reference") or raw.get("invoiceId") or raw.get("id") or invoice_uuid,
            "qr": raw.get("qrCode") or raw.get("qr") or "",
            "raw": raw,
        }

    def check_status(self, reference: str) -> dict[str, Any]:
        if not reference:
            raise ValueError("reference is required")
        client, owned = self._get_client()
        try:
            url = f"{self.base_url}{self.STATUS_PATH.format(reference=reference)}"
            resp = client.get(
                url, headers=self._headers(client, content_type="application/json"), timeout=self.timeout
            )
        finally:
            if owned:
                client.close()
        logger.info("jofotara.status reference=%s http=%s", reference, resp.status_code)
        resp.raise_for_status()
        raw = _safe_json(resp)
        return {"status": raw.get("status", "unknown"), "reference": reference,
                "qr": raw.get("qrCode") or raw.get("qr") or "", "raw": raw}


def _safe_json(resp: httpx.Response) -> dict[str, Any]:
    try:
        data = resp.json()
    except ValueError:
        return {"text": resp.text}
    return data if isinstance(data, dict) else {"data": data}


__all__ = ["JoFotaraClient"]
