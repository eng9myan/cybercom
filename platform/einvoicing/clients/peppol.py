"""
Peppol Access Point transport client.

Peppol is a four-corner network: a sender never talks to a tax authority
directly, it hands the document to a *certified Access Point* which routes
it over AS4 to the receiver's AP, discovered via SMP. Running an AP requires
certification and a PKI certificate from OpenPeppol, so in practice a tenant
subscribes to a commercial AP (Storecove, Tickstar/Pagero, Unimaze, ...).

This client is therefore a thin, provider-agnostic HTTP seam over "whatever
AP the tenant bought", configured by env -- the same shape as the JoFotara
client and the HyperPay/SMS provider seams elsewhere in the platform.

Deliberately honest about the boundary: with no AP configured, `submit`
raises `PeppolNotConfigured` rather than returning a fake "cleared". The
document builder (platform.einvoicing.ubl.build_peppol_ubl) is real and
standards-conformant and can be generated, validated and exported with no
AP at all -- what needs a commercial account is *transmission*, not the
invoice itself.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("platform.einvoicing.peppol")

DEFAULT_TIMEOUT = 30.0


class PeppolNotConfigured(RuntimeError):
    """No Access Point credentials configured for this deployment."""


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


class PeppolClient:
    """Generic REST Access Point client.

    Expects the AP to accept a document + routing metadata and return a
    reference. Endpoint/paths are configurable because every AP vendor's
    REST surface differs -- the parts that are standardised (the UBL, the
    participant identifiers) are handled upstream of this class.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        submit_path: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = (base_url or _env("PEPPOL_AP_BASE_URL")).rstrip("/")
        self.api_key = api_key or _env("PEPPOL_AP_API_KEY")
        self.submit_path = submit_path or _env("PEPPOL_AP_SUBMIT_PATH", "/documents")
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def submit(self, xml: str, *, sender_id: str, receiver_id: str, doc_id: str) -> dict[str, Any]:
        if not self.configured:
            raise PeppolNotConfigured(
                "No Peppol Access Point configured. Set PEPPOL_AP_BASE_URL and "
                "PEPPOL_AP_API_KEY to a certified AP subscription to transmit; "
                "the EN 16931 document itself is generated and stored regardless."
            )
        resp = httpx.post(
            f"{self.base_url}{self.submit_path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/xml",
                "X-Peppol-Sender": sender_id,
                "X-Peppol-Receiver": receiver_id,
                "X-Peppol-Document-Id": doc_id,
            },
            content=xml.encode("utf-8"),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        body = resp.json() if resp.content else {}
        return {
            "status": body.get("status", "submitted"),
            "reference": body.get("id") or body.get("reference", ""),
            "qr": "",
            "raw": body,
        }
