"""
AI-assisted document field extraction (invoice/PO/bank-statement parsing),
via the Claude API's vision input -- Anthropic's own model, same posture as
the JoFotara/HyperPay/Peppol provider seams elsewhere in the platform: a
thin, provider-agnostic HTTP call configured entirely by env, honest about
the boundary. With no API key configured, `extract()` raises
`DocAIExtractionNotConfigured` rather than faking a result.

This never posts anything: it returns a plain dict of whatever the model
read off the page, for a human to review and correct (ParsedDocument.status
'parsed', not 'reviewed'). Creating a real Invoice/PurchaseOrder from
reviewed data is a separate, explicit action elsewhere -- not this module's
job, and not attempted here.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re

import httpx

logger = logging.getLogger("products.cycom.docai")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5"
REQUEST_TIMEOUT = 60.0

SUPPORTED_MEDIA_TYPES = {
    "application/pdf": "document",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
}

# Field shape per document type. The prompt tells the model to use null for
# anything it can't confidently read rather than guessing -- a wrong number
# silently posted into accounting data is worse than an honest gap a human
# has to fill in.
_SCHEMAS = {
    "invoice": {
        "vendor_name": "string or null",
        "invoice_number": "string or null",
        "invoice_date": "YYYY-MM-DD or null",
        "due_date": "YYYY-MM-DD or null",
        "currency": "3-letter code or null",
        "subtotal": "number or null",
        "tax_amount": "number or null",
        "total_amount": "number or null",
        "line_items": [{"description": "string", "quantity": "number or null", "unit_price": "number or null", "amount": "number or null"}],
    },
    "purchase_order": {
        "vendor_name": "string or null",
        "po_number": "string or null",
        "order_date": "YYYY-MM-DD or null",
        "currency": "3-letter code or null",
        "total_amount": "number or null",
        "line_items": [{"description": "string", "quantity": "number or null", "unit_price": "number or null", "amount": "number or null"}],
    },
    "bank_statement": {
        "account_number": "string or null",
        "statement_period_start": "YYYY-MM-DD or null",
        "statement_period_end": "YYYY-MM-DD or null",
        "currency": "3-letter code or null",
        "opening_balance": "number or null",
        "closing_balance": "number or null",
        "transactions": [{"date": "YYYY-MM-DD", "description": "string", "amount": "number", "type": "debit or credit"}],
    },
}


class DocAIExtractionNotConfigured(RuntimeError):
    """No Anthropic API key configured for this deployment."""


class DocAIExtractionError(RuntimeError):
    """The API call succeeded but the response wasn't usable (bad JSON, unexpected shape)."""


def _api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "")


def _build_prompt(document_type: str) -> str:
    schema = _SCHEMAS[document_type]
    return (
        f"Extract the following fields from this {document_type.replace('_', ' ')}. "
        "Respond with ONLY a single JSON object matching exactly this shape "
        "(no markdown fences, no commentary):\n\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Use null for any field you cannot confidently read from the document -- "
        "never guess or estimate a number. If the document has multiple line "
        "items/transactions, include every one you can read."
    )


def _extract_json(text: str) -> dict:
    # Models sometimes wrap JSON in a ```json fence despite instructions not
    # to -- strip it rather than failing the whole extraction over formatting.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise DocAIExtractionError("The model's response did not contain a JSON object.")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise DocAIExtractionError(f"The model's response was not valid JSON: {exc}") from exc


def extract(*, document_type: str, file_bytes: bytes, media_type: str) -> dict:
    """Calls the Claude API with the document's bytes and returns the
    extracted fields as a plain dict. Raises DocAIExtractionNotConfigured or
    DocAIExtractionError on failure -- callers persist that as a failed
    ParsedDocument rather than letting it propagate as a 500."""
    if document_type not in _SCHEMAS:
        raise ValueError(f"Unknown document_type '{document_type}'.")

    block_type = SUPPORTED_MEDIA_TYPES.get(media_type)
    if block_type is None:
        raise DocAIExtractionError(
            f"Unsupported file type '{media_type}'. Supported: {', '.join(SUPPORTED_MEDIA_TYPES)}."
        )

    api_key = _api_key()
    if not api_key:
        raise DocAIExtractionNotConfigured(
            "AI document parsing is not configured for this deployment. Set ANTHROPIC_API_KEY."
        )

    encoded = base64.b64encode(file_bytes).decode("ascii")
    payload = {
        "model": os.getenv("ANTHROPIC_DOCAI_MODEL", DEFAULT_MODEL),
        "max_tokens": 4096,
        "messages": [{
            "role": "user",
            "content": [
                {"type": block_type, "source": {"type": "base64", "media_type": media_type, "data": encoded}},
                {"type": "text", "text": _build_prompt(document_type)},
            ],
        }],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_API_VERSION,
        "content-type": "application/json",
    }

    try:
        resp = httpx.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.warning("docai: Claude API returned %s: %s", exc.response.status_code, exc.response.text[:500])
        raise DocAIExtractionError(f"The AI service returned an error ({exc.response.status_code}).") from exc
    except httpx.HTTPError as exc:
        raise DocAIExtractionError(f"Could not reach the AI service: {exc}") from exc

    data = resp.json()
    try:
        text = data["content"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DocAIExtractionError("Unexpected response shape from the AI service.") from exc

    return _extract_json(text)
