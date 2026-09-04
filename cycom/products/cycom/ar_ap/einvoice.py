"""
Bridge: a posted CyCom AR Invoice → platform.einvoicing clearance engine.

Maps the invoice + its lines + the tenant's own profile into the engine's
input, runs clearance, and writes the result back onto the Invoice's
`einvoice_*` fields. Guarded — a failure here never propagates (JO policy:
clearance is downstream of a real GL entry that already exists).
"""
from __future__ import annotations

import logging
from datetime import datetime, time

from django.utils import timezone

from platform.einvoicing.engine import SellerProfile, clear_invoice, mode_for_country
from platform.tenant.models import Tenant, TenantProfile

logger = logging.getLogger("cycom.ar_ap.einvoice")


def _seller_for(tenant_id) -> tuple[SellerProfile, str]:
    """Return (SellerProfile, country_code) for the issuing tenant."""
    tenant = Tenant.objects.filter(id=tenant_id).first()
    country = (getattr(tenant, "country_code", "") or "").upper()
    profile = TenantProfile.objects.filter(tenant_id=tenant_id).first()
    seller = SellerProfile(
        tin=(getattr(profile, "vat_number", "") or "").strip(),
        name=(getattr(profile, "legal_name", "") or getattr(tenant, "name", "") or "").strip(),
        city=(getattr(profile, "city", "") or ""),
    )
    return seller, country


def run_einvoice_clearance(invoice) -> None:
    seller, country = _seller_for(invoice.tenant_id)
    mode = mode_for_country(country)
    if mode not in ("jo_jofotara", "sa_zatca"):
        # AE (Peppol) raises NotImplementedError in the engine; everything else
        # has no e-invoicing mandate. Leave einvoice_status="none".
        return

    # SA: a customer invoice with a buyer VAT number is a standard (B2B) invoice
    # -> ZATCA clearance (blocking); without one it's simplified (B2C) -> reporting.
    is_simplified = mode == "sa_zatca" and not (invoice.partner.tax_id or "").strip()

    issue_dt = datetime.combine(invoice.date, time(12, 0))
    lines = [
        {
            "name": ln.description or "Item",
            "quantity": ln.quantity,
            "unit_price": ln.unit_price,
            "tax_percent": ln.tax_percent,
        }
        for ln in invoice.lines.all()
    ]

    try:
        result = clear_invoice(
            tenant_id=invoice.tenant_id,
            scope="default",                       # per-org sequences come with multi-company
            country_code=country,
            number=invoice.number,
            issue_dt=issue_dt,
            currency=invoice.currency,
            seller=seller,
            buyer_tin=(invoice.partner.tax_id or ""),
            buyer_name=invoice.partner.name,
            buyer_city=getattr(invoice.partner, "city", ""),
            lines=lines,
            is_simplified=is_simplified,
        )
    except Exception:
        logger.exception("e-invoice clearance failed for %s", invoice.number)
        invoice.einvoice_status = "rejected"
        invoice.save(update_fields=["einvoice_status", "updated_at"])
        return

    invoice.einvoice_mode = result.mode
    invoice.einvoice_uuid = result.uuid
    invoice.einvoice_icv = result.icv
    invoice.einvoice_pih = result.pih
    invoice.einvoice_hash = result.invoice_hash
    invoice.einvoice_qr = result.qr
    # persist the authority's own outcome (cleared | reported | submitted); a
    # non-ok status (e.g. ZATCA "INVALID", transport error) reads as "rejected"
    invoice.einvoice_status = result.status if result.ok else "rejected"
    invoice.einvoice_reference = result.provider_reference
    invoice.einvoice_response = {"error": result.error} if result.error else {}
    invoice.einvoice_cleared_at = timezone.now() if result.ok else None
    invoice.save(update_fields=[
        "einvoice_mode", "einvoice_uuid", "einvoice_icv", "einvoice_pih",
        "einvoice_hash", "einvoice_qr", "einvoice_status", "einvoice_reference",
        "einvoice_response", "einvoice_cleared_at", "updated_at",
    ])
