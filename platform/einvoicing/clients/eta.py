"""
ETA (Egyptian Tax Authority) e-invoicing transport client.

Direct government API, like JoFotara/ZATCA -- no intermediary. OAuth2
client_credentials against the ETA Identity Service, then a JSON document
submission against the e-invoicing API.

Base URLs and the exact token path are reconstructed from the published ETA
SDK docs (sdk.invoicing.eta.gov.eg) -- the full OpenAPI spec is only handed
out during taxpayer onboarding on the preprod portal, which this session
has no account for. Submit path and response shape
(submissionUUID/acceptedDocuments/rejectedDocuments) are taken verbatim from
the SDK's own published page; the token endpoint is reconstructed from the
documented hostnames (id.eta.gov.eg / id.preprod.eta.gov.eg) and the
client_credentials grant convention every other ETA integration describes.
**Not verified against the live sandbox** -- same caveat as this engine's
other formats where the real field spec isn't fully public (c.f. the India
GST schema's own $comment).
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("platform.einvoicing.eta")

DEFAULT_BASE_URL = "https://api.preprod.invoicing.eta.gov.eg"
DEFAULT_TOKEN_URL = "https://id.preprod.eta.gov.eg/connect/token"
DEFAULT_TIMEOUT = 30.0


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


class EtaClient:
    SUBMIT_PATH = "/api/v1.0/documentsubmissions/"
    GET_DOCUMENT_PATH = "/api/v1.0/documents/{uuid}/raw"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or _env("ETA_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.token_url = token_url or _env("ETA_TOKEN_URL", DEFAULT_TOKEN_URL)
        self.client_id = client_id or _env("ETA_CLIENT_ID")
        self.client_secret = client_secret or _env("ETA_CLIENT_SECRET")
        self.timeout = timeout
        self._injected_client = client

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_client(self) -> tuple[httpx.Client, bool]:
        if self._injected_client is not None:
            return self._injected_client, False
        return httpx.Client(timeout=self.timeout), True

    def _bearer_token(self, client: httpx.Client) -> str:
        resp = client.post(
            self.token_url,
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
            raise RuntimeError("ETA identity service returned an empty access_token")
        return token

    def _headers(self, client: httpx.Client) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self._bearer_token(client)}",
        }

    def submit_document(self, document_json: str, internal_id: str) -> dict[str, Any]:
        """Submit one signed document. ETA's submit endpoint takes a batch
        (`{"documents": [...]}`) even for a single document."""
        import json

        if not isinstance(document_json, str) or not document_json.strip():
            raise ValueError("document_json must be a non-empty JSON string")
        body = {"documents": [json.loads(document_json)["document"]]}

        client, owned = self._get_client()
        try:
            resp = client.post(
                f"{self.base_url}{self.SUBMIT_PATH}",
                json=body,
                headers=self._headers(client),
                timeout=self.timeout,
            )
        finally:
            if owned:
                client.close()

        logger.info("eta.submit internal_id=%s http=%s", internal_id, resp.status_code)
        resp.raise_for_status()
        raw = _safe_json(resp)
        accepted = raw.get("acceptedDocuments") or []
        rejected = raw.get("rejectedDocuments") or []
        match = next((a for a in accepted if a.get("internalId") == internal_id), accepted[0] if accepted else {})
        if rejected and not accepted:
            err = rejected[0].get("error", {})
            return {"status": "rejected", "reference": internal_id, "error": err, "raw": raw}
        return {
            "status": "submitted" if match else "error",
            "reference": match.get("uuid", internal_id),
            "long_id": match.get("longId", ""),
            "submission_uuid": raw.get("submissionUUID", ""),
            "raw": raw,
        }

    def check_status(self, uuid: str) -> dict[str, Any]:
        if not uuid:
            raise ValueError("uuid is required")
        client, owned = self._get_client()
        try:
            url = f"{self.base_url}{self.GET_DOCUMENT_PATH.format(uuid=uuid)}"
            resp = client.get(url, headers=self._headers(client), timeout=self.timeout)
        finally:
            if owned:
                client.close()
        logger.info("eta.status uuid=%s http=%s", uuid, resp.status_code)
        resp.raise_for_status()
        raw = _safe_json(resp)
        return {"status": raw.get("status", "unknown"), "reference": uuid, "raw": raw}


def _safe_json(resp: httpx.Response) -> dict[str, Any]:
    try:
        data = resp.json()
    except ValueError:
        return {"text": resp.text}
    return data if isinstance(data, dict) else {"data": data}


__all__ = ["EtaClient"]
