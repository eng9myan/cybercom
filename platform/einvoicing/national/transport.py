"""
Provider-agnostic transmission seam for national e-invoicing channels.

Almost every national mandate is reached through a certified intermediary
in practice, not by a taxpayer's own direct connection: an SdI channel or
intermediary (IT), a PAC (MX), a GSP/IRP gateway (IN), a KSeF integrator
(PL), a SEFAZ-connected provider (BR), an SII/AEAT gateway (ES). Their REST
surfaces all differ, so -- like the Peppol Access Point client -- this is a
thin HTTP seam configured per format by env (`<PREFIX>_BASE_URL`,
`<PREFIX>_API_KEY`, optional `<PREFIX>_SUBMIT_PATH`) that posts the
finished document and returns the provider's reference.

With nothing configured, `submit` raises TransportNotConfigured. It never
returns a fake acceptance.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from .base import TransportNotConfigured

DEFAULT_TIMEOUT = 30.0


class IntermediaryClient:
    def __init__(self, env_prefix: str, *, channel_label: str, timeout: float = DEFAULT_TIMEOUT,
                 content_type: str = "application/xml"):
        self.env_prefix = env_prefix
        self.channel_label = channel_label
        self.base_url = os.getenv(f"{env_prefix}_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv(f"{env_prefix}_API_KEY", "")
        self.submit_path = os.getenv(f"{env_prefix}_SUBMIT_PATH", "/documents")
        self.timeout = timeout
        self.content_type = content_type

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def submit(self, document: str, *, filename: str, doc=None) -> dict[str, Any]:
        if not self.configured:
            raise TransportNotConfigured(
                f"No {self.channel_label} configured. Set {self.env_prefix}_BASE_URL and "
                f"{self.env_prefix}_API_KEY to transmit; the document itself was generated "
                "and stored and can be downloaded and filed manually."
            )
        resp = httpx.post(
            f"{self.base_url}{self.submit_path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": self.content_type,
                "X-Document-Filename": filename,
            },
            content=document.encode("utf-8"),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        body = resp.json() if resp.content else {}
        return {
            "status": body.get("status", "submitted"),
            "reference": body.get("id") or body.get("reference", ""),
            "qr": body.get("qr", ""),
            "raw": body,
        }
