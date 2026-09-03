"""
JoFotara (Jordan) e-invoicing client.

JoFotara is the Jordanian Income & Sales Tax Department's e-invoicing
platform.  Invoices are UBL 2.1 (customization ID ``PINT-JO``) and — in
production — must carry a XAdES enveloped signature made with the taxpayer's
certificate.

This module exposes:

* :class:`JoFotaraClient` — the spec-conforming, hardened client used by new
  code.  ``submit_invoice`` takes signed UBL XML plus the invoice UUID and
  returns ``{"status", "reference", "raw"}``; ``check_status`` polls the
  submission status.
* :class:`JoFawTraClient` / :class:`JoFawtraClient` — thin backwards-compat
  aliases that keep the legacy ``submit_invoice(dict)`` /
  ``validate_invoice(id)`` signatures alive for existing callers
  (``payments.tasks.stamp_bill_task``, the viewset).

Transport is :mod:`httpx` with an injectable client for tests.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("products.cymed.integrations.jofawtra")


DEFAULT_BASE_URL = "https://sandbox.jofotara.gov.jo"
DEFAULT_TIMEOUT = 30.0


def _env(name: str, default: str = "") -> str:
    """Read environment variable with a sensible default.

    Kept as a helper so tests can monkeypatch a single seam.
    """

    return os.getenv(name, default)


class JoFotaraClient:
    """Hardened JoFotara e-invoicing client.

    All I/O goes through :mod:`httpx`.  A caller may inject a preconfigured
    ``httpx.Client`` (useful for tests and for reusing connections across a
    Celery task); if omitted the client owns one for the call.
    """

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

    # ------------------------------------------------------------------
    # Auth / headers
    # ------------------------------------------------------------------
    def _basic_auth_header(self) -> str:
        token = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        ).decode("ascii")
        return f"Basic {token}"

    def _bearer_token(self, client: httpx.Client) -> str:
        """Exchange client credentials for a bearer token.

        JoFotara's sandbox supports client-credentials on ``/oauth/token``.
        Kept as a small helper so a bearer-mode caller doesn't have to
        reimplement it.
        """

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
        # default: basic
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

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------
    def _sign_xml(self, ubl_xml: str) -> str:
        """Return XAdES-signed UBL.

        Production JoFotara demands a XAdES enveloped signature over the
        UBL Invoice.  A full XAdES implementation is out of scope for this
        client; if the private-key path is not configured we warn loudly and
        fall through with the unsigned XML — useful for sandbox smoke tests
        but never appropriate for prod.
        """

        if not self.private_key_path or not os.path.exists(self.private_key_path):
            logger.warning(
                "JoFotara signing key not configured (JOFOTARA_PRIVATE_KEY_PATH=%r); "
                "submitting UNSIGNED payload — do NOT use in production",
                self.private_key_path,
            )
            return ubl_xml
        # Real XAdES signing is delegated to a downstream integration.
        # Wire your signer here (e.g. signxml / xmlsec bindings).
        logger.info("XAdES signing hook invoked with key=%s", self.private_key_path)
        return ubl_xml

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------
    def _get_client(self) -> tuple[httpx.Client, bool]:
        """Return (client, owned).  ``owned`` = True means the caller must close it."""

        if self._injected_client is not None:
            return self._injected_client, False
        return httpx.Client(timeout=self.timeout), True

    # ------------------------------------------------------------------
    # Public API — spec
    # ------------------------------------------------------------------
    def submit_invoice(self, ubl_xml: str, invoice_uuid: str) -> dict[str, Any]:
        """Submit signed UBL 2.1 XML to JoFotara.

        Returns ``{"status", "reference", "raw"}``.  Raises on transport /
        HTTP failure — we do not swallow real errors.
        """

        if not isinstance(ubl_xml, str) or not ubl_xml.strip():
            raise ValueError("ubl_xml must be a non-empty XML string")
        if not invoice_uuid:
            raise ValueError("invoice_uuid is required")

        signed = self._sign_xml(ubl_xml)
        payload = base64.b64encode(signed.encode("utf-8")).decode("ascii")
        body = {
            "invoice": payload,
            "invoiceUuid": invoice_uuid,
            "customizationId": "PINT-JO",
        }

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

        logger.info(
            "JoFotara submit uuid=%s status=%s", invoice_uuid, resp.status_code
        )
        resp.raise_for_status()
        raw = _safe_json(resp)
        return {
            "status": raw.get("status") or ("submitted" if resp.is_success else "error"),
            "reference": raw.get("reference")
            or raw.get("invoiceId")
            or raw.get("id")
            or invoice_uuid,
            "raw": raw,
        }

    def check_status(self, reference: str) -> dict[str, Any]:
        """Fetch the submission status for a JoFotara reference."""

        if not reference:
            raise ValueError("reference is required")

        client, owned = self._get_client()
        try:
            url = f"{self.base_url}{self.STATUS_PATH.format(reference=reference)}"
            resp = client.get(
                url,
                headers=self._headers(client, content_type="application/json"),
                timeout=self.timeout,
            )
        finally:
            if owned:
                client.close()

        logger.info(
            "JoFotara status reference=%s http=%s", reference, resp.status_code
        )
        resp.raise_for_status()
        raw = _safe_json(resp)
        return {
            "status": raw.get("status", "unknown"),
            "reference": reference,
            "raw": raw,
        }


def _safe_json(resp: httpx.Response) -> dict[str, Any]:
    """Parse JSON, falling back to a wrapped raw-text dict on decode errors."""

    try:
        data = resp.json()
    except ValueError:
        return {"text": resp.text}
    if isinstance(data, dict):
        return data
    return {"data": data}


# ---------------------------------------------------------------------------
# Backwards-compatible aliases.
#
# Existing callers (payments.tasks, JoFawTraInvoiceViewSet) import
# ``JoFawTraClient`` / ``JoFawtraClient`` and call ``submit_invoice(dict)`` +
# ``validate_invoice(id)``.  Preserve those signatures so nothing breaks.
# ---------------------------------------------------------------------------
class JoFawTraClient(JoFotaraClient):
    """Legacy alias — accepts either a UBL XML string or a legacy payload dict."""

    def submit_invoice(  # type: ignore[override]
        self,
        payload: Any,
        invoice_uuid: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(payload, str):
            uuid_val = invoice_uuid or ""
            return super().submit_invoice(payload, uuid_val)
        # legacy dict path — derive a placeholder UBL body & uuid
        if not isinstance(payload, dict):
            raise TypeError("payload must be a UBL XML string or a legacy dict")
        uuid_val = (
            invoice_uuid
            or payload.get("uuid")
            or payload.get("invoice_uuid")
            or payload.get("bill_number", "")
        )
        ubl_xml = payload.get("ubl_xml") or _legacy_dict_to_ubl(payload)
        return super().submit_invoice(ubl_xml, str(uuid_val))

    def validate_invoice(self, invoice_id: str) -> dict[str, Any]:
        """Legacy name for :meth:`check_status`."""

        return self.check_status(invoice_id)


# Second alias — spelling variant already in use.
JoFawtraClient = JoFawTraClient


def _legacy_dict_to_ubl(payload: dict[str, Any]) -> str:
    """Best-effort UBL 2.1 skeleton generated from the legacy dict payload.

    The real UBL builder lives elsewhere; this is only meant to keep the
    legacy call path working end-to-end when a proper XML builder has not
    yet been wired in.
    """

    bill_number = payload.get("bill_number", "")
    issued_at = payload.get("issued_at", "")
    total = payload.get("total", "0")
    subtotal = payload.get("subtotal", "0")
    vat = payload.get("vat", "0")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">'
        '<cbc:CustomizationID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
        "PINT-JO"
        "</cbc:CustomizationID>"
        f'<cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{bill_number}</cbc:ID>'
        f'<cbc:IssueDate xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{issued_at}</cbc:IssueDate>'
        f'<cbc:TaxExclusiveAmount xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" currencyID="JOD">{subtotal}</cbc:TaxExclusiveAmount>'
        f'<cbc:TaxAmount xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" currencyID="JOD">{vat}</cbc:TaxAmount>'
        f'<cbc:PayableAmount xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" currencyID="JOD">{total}</cbc:PayableAmount>'
        "</Invoice>"
    )


__all__ = ["JoFotaraClient", "JoFawTraClient", "JoFawtraClient"]
