"""
CyID ecosystem, Phase 6 — posts a finalized invoice to the compliance
gateway for country-specific e-invoicing formatting (JoFotara/ZATCA/Peppol).
compliance-gateway is a separate FastAPI microservice — real network
boundary, not a Python import, same pattern as cymart's cydrive_client.py.

Calls the gateway's direct REST endpoint (POST /api/compliance/process),
not its EventBus subscription — that subscription is dead code today
(imports core-kernel's `bus` module, fully decommissioned this session;
see core/settings.py's COMPLIANCE_GATEWAY_URL comment). Failures here are
logged, not raised — compliance formatting is a downstream concern that
must never block or roll back a real GL-posted invoice.
"""

import logging
from decimal import Decimal

import httpx
from django.conf import settings

logger = logging.getLogger("cycom.compliance_integration")


def _money(value: Decimal) -> str:
    # Invoice.amount_* are DecimalField(decimal_places=2) — that constraint
    # only applies at DB serialization, not to an in-memory value computed
    # via sum()/division just before this call, which can carry extra
    # decimal places. Quantize explicitly so government e-invoicing
    # endpoints downstream never see "116.000000" for a 2-decimal currency.
    return str(value.quantize(Decimal("0.01")))


def notify_invoice_finalized(invoice, jurisdiction) -> dict | None:
    payload = {
        "region": jurisdiction.compliance_region,
        "tenant_id": str(invoice.tenant_id),
        "company_id": str(invoice.tenant_id),
        "invoice": {
            "number": invoice.number,
            "date": invoice.date.isoformat(),
            "currency": invoice.currency,
            "amount_subtotal": _money(invoice.amount_subtotal),
            "amount_tax": _money(invoice.amount_tax),
            "amount_total": _money(invoice.amount_total),
            "partner_name": invoice.partner.name,
            "partner_tax_id": invoice.partner.tax_id,
        },
    }
    url = f"{settings.COMPLIANCE_GATEWAY_URL}/api/compliance/process"
    try:
        response = httpx.post(url, json=payload, timeout=settings.COMPLIANCE_GATEWAY_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        logger.error(
            "Compliance gateway notification failed for invoice %s (region=%s): %s",
            invoice.number,
            jurisdiction.compliance_region,
            exc,
        )
        return None
