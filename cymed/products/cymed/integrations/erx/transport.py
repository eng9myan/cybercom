"""
Network transport. Every network is a FHIR-messaging POST to an endpoint the
deployment configures:

    CYMED_ERX_<NETWORK>_URL     e.g. CYMED_ERX_WASFATY_URL
    CYMED_ERX_<NETWORK>_TOKEN   bearer token (or use mTLS below)
    CYMED_ERX_<NETWORK>_CERT / _KEY   client certificate pair, when required

Network onboarding (registration, test scripts, certificates) is done with
each operator; until a URL is configured the network answers
``not_configured`` and nothing is pretended.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class TransportResult:
    status: str  # accepted | rejected | sent | failed | not_configured
    detail: str = ""
    response: dict | None = None
    external_id: str = ""


def _env(network: str, key: str) -> str:
    return os.environ.get(f"CYMED_ERX_{network.upper()}_{key}", "").strip()


def is_configured(network: str) -> bool:
    return bool(_env(network, "URL"))


def send(network: str, bundle: dict, *, timeout: float = 20.0) -> TransportResult:
    url = _env(network, "URL")
    if not url:
        return TransportResult("not_configured",
                               f"Set CYMED_ERX_{network.upper()}_URL (and credentials) to transmit via {network}.")
    headers = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
    token = _env(network, "TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    cert = (_env(network, "CERT"), _env(network, "KEY"))
    try:
        with httpx.Client(timeout=timeout, cert=cert if all(cert) else None) as client:
            resp = client.post(url, json=bundle, headers=headers)
    except httpx.HTTPError as exc:
        return TransportResult("failed", f"Transport error: {exc.__class__.__name__}")
    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text[:2000]}
    if resp.status_code >= 500:
        return TransportResult("failed", f"Network returned HTTP {resp.status_code}", body)
    if resp.status_code >= 400:
        return TransportResult("rejected", _outcome_text(body) or f"HTTP {resp.status_code}", body)
    if resp.status_code == 202:
        return TransportResult("sent", "Accepted for asynchronous processing", body, _ext_id(body))
    return TransportResult("accepted", "", body, _ext_id(body))


def _outcome_text(body: dict) -> str:
    """Pull the issue text out of an OperationOutcome (top level or in a response bundle)."""
    resources = [body] + [e.get("resource", {}) for e in body.get("entry", []) if isinstance(e, dict)]
    for r in resources:
        if r.get("resourceType") == "OperationOutcome":
            return "; ".join(i.get("diagnostics") or i.get("details", {}).get("text", "") or i.get("code", "")
                             for i in r.get("issue", []))
    return ""


def _ext_id(body: dict) -> str:
    return str(body.get("id") or "")
