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
from decimal import Decimal

from django.utils import timezone

from platform.einvoicing.engine import (
    NATIONAL_FORMATS,
    SellerProfile,
    clear_invoice,
    clear_national,
    mode_for_country,
    resubmit_national,
)
from platform.einvoicing.models import EInvoiceInteraction, EInvoiceProfile
from platform.einvoicing.national import DocInput, LineInput, PartyInput
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


EINVOICE_ATTR = "einvoice"   # key inside Partner/Invoice/InvoiceLine.attributes


def national_seller_party(tenant_id, country: str) -> PartyInput:
    """Seller identity for a national format: the tenant's EInvoiceProfile,
    with legal name / VAT number falling back to TenantProfile."""
    tenant = Tenant.objects.filter(id=tenant_id).first()
    tprofile = TenantProfile.objects.filter(tenant_id=tenant_id).first()
    ep = EInvoiceProfile.objects.filter(tenant_id=tenant_id).first()
    return PartyInput(
        tax_id=((ep and ep.tax_id) or getattr(tprofile, "vat_number", "") or "").strip(),
        name=((ep and ep.legal_name) or getattr(tprofile, "legal_name", "")
              or getattr(tenant, "name", "") or "").strip(),
        street=(ep.street if ep else ""), building_number=(ep.building_number if ep else ""),
        city=(ep.city if ep else ""), postal_code=(ep.postal_code if ep else ""),
        region=(ep.region if ep else ""), email=(ep.email if ep else ""),
        country_code=country,
        extra=dict(ep.national) if ep else {},
    )


def national_buyer_party(partner) -> PartyInput:
    """Buyer identity: the Partner's own columns, overridden/extended by the
    national keys stored in partner.attributes["einvoice"]. No country is
    assumed -- a format that needs one asks for it."""
    attrs = dict((partner.attributes or {}).get(EINVOICE_ATTR, {}))
    core = {k: attrs.pop(k) for k in list(attrs)
            if k in ("tax_id", "name", "street", "building_number", "city", "postal_code",
                     "region", "country_code", "email")}
    return PartyInput(
        tax_id=core.get("tax_id", partner.tax_id or ""),
        name=core.get("name", partner.name or ""),
        street=core.get("street", getattr(partner, "address", "") or ""),
        building_number=core.get("building_number", ""),
        city=core.get("city", partner.city or ""),
        postal_code=core.get("postal_code", ""),
        region=core.get("region", ""),
        country_code=(core.get("country_code") or "").upper(),
        email=core.get("email", getattr(partner, "email", "") or ""),
        extra=attrs,
    )


def national_doc_input(invoice, country: str) -> DocInput:
    lines = [
        LineInput(
            name=ln.description or "Item",
            quantity=Decimal(ln.quantity), unit_price=Decimal(ln.unit_price),
            tax_percent=Decimal(ln.tax_percent),
            extra=dict((ln.attributes or {}).get(EINVOICE_ATTR, {})),
        )
        for ln in invoice.lines.all()
    ]
    original = invoice.reverses
    return DocInput(
        number=invoice.number,
        issue_dt=datetime.combine(invoice.date, time(12, 0)),
        currency=invoice.currency,
        seller=national_seller_party(invoice.tenant_id, country),
        buyer=national_buyer_party(invoice.partner),
        lines=lines,
        is_credit_note=invoice.invoice_type in ("customer_credit_note",),
        original_number=original.number if original else "",
        original_date=original.date if original else None,
        due_date=invoice.due_date,
        extra={
            # the corrected invoice's authority id (e.g. its KSeF number)
            **({"original_reference": original.einvoice_reference} if original and original.einvoice_reference else {}),
            **dict((invoice.attributes or {}).get(EINVOICE_ATTR, {})),
        },
    )


def _save_national_result(invoice, result) -> None:
    if result.status == "not_applicable":
        # Outside the mandate (e.g. an Indian B2C sale): nothing to issue.
        invoice.einvoice_mode = result.mode
        invoice.einvoice_status = "not_applicable"
        invoice.einvoice_response = {"note": result.error}
        invoice.save(update_fields=["einvoice_mode", "einvoice_status", "einvoice_response", "updated_at"])
        return
    invoice.einvoice_mode = result.mode
    invoice.einvoice_uuid = result.uuid if result.status != "incomplete" else None
    invoice.einvoice_icv = result.icv or None
    invoice.einvoice_pih = result.pih
    invoice.einvoice_hash = result.invoice_hash
    invoice.einvoice_qr = result.qr
    invoice.einvoice_status = result.status if (result.ok or result.status in ("generated", "incomplete")) \
        else "rejected"
    invoice.einvoice_reference = result.provider_reference
    response = {}
    if result.problems:
        response["problems"] = result.problems
    if result.error:
        response["error"] = result.error
    invoice.einvoice_response = response
    invoice.einvoice_cleared_at = timezone.now() if result.ok else None
    invoice.save(update_fields=[
        "einvoice_mode", "einvoice_uuid", "einvoice_icv", "einvoice_pih",
        "einvoice_hash", "einvoice_qr", "einvoice_status", "einvoice_reference",
        "einvoice_response", "einvoice_cleared_at", "updated_at",
    ])


def run_national_clearance(invoice, mode: str, country: str) -> None:
    try:
        result = clear_national(tenant_id=invoice.tenant_id, scope="default", mode=mode,
                                doc=national_doc_input(invoice, country))
    except Exception:
        logger.exception("national e-invoice (%s) failed for %s", mode, invoice.number)
        invoice.einvoice_mode = mode
        invoice.einvoice_status = "rejected"
        invoice.save(update_fields=["einvoice_mode", "einvoice_status", "updated_at"])
        return
    _save_national_result(invoice, result)


def resubmit_generated(invoice) -> None:
    """Transmit a 'generated' document that couldn't be sent earlier, without
    rebuilding it (it already carries its progressive)."""
    interaction = (EInvoiceInteraction.objects
                   .filter(tenant_id=invoice.tenant_id, mode=invoice.einvoice_mode,
                           invoice_ref=invoice.number, status="generated")
                   .order_by("-created_at").first())
    if interaction is None:
        return
    _seller, country = _seller_for(invoice.tenant_id)
    result = resubmit_national(interaction=interaction, doc=national_doc_input(invoice, country))
    _save_national_result(invoice, result)


def run_einvoice_clearance(invoice) -> None:
    seller, country = _seller_for(invoice.tenant_id)
    mode = mode_for_country(country)
    if mode in NATIONAL_FORMATS:
        run_national_clearance(invoice, mode, country)
        return
    if mode not in ("jo_jofotara", "sa_zatca", "eu_peppol"):
        # No e-invoicing mandate mapped for this country -- leave
        # einvoice_status="none" rather than guessing at a format.
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
