"""
E-invoicing clearance orchestration.

`clear_invoice(invoice)` — the one entry point product code calls after an
invoice is finalised:

    1. resolve the mode from the tenant's country (jo_jofotara | sa_zatca | ...)
    2. lock the (tenant, scope) sequence row, take the next ICV + the PIH
    3. build the UBL 2.1 document for that mode
    4. compute this invoice's hash, advance the chain
    5. submit to the authority (JoFotara / ZATCA / Peppol AP)
    6. persist the result on the Invoice + write an EInvoiceInteraction
    7. commit the sequence advance only if submission did not hard-fail

For JO the call is non-blocking by policy — a rejected/failed clearance sets
`einvoice_status="rejected"` and is surfaced in the UI, but never rolls back
the GL-posted invoice (matches the existing compliance_client.py contract).
For SA B2B clearance (planned) the invoice is not valid to send until cleared.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from django.db import transaction
from django.utils import timezone

from .clients.jofotara import JoFotaraClient
from .hashing import invoice_hash
from .models import EInvoiceInteraction, EInvoiceSequence
from .signing import get_signer
from .ubl import JoInvoiceData, UblLine, UblParty, build_jo_ubl

logger = logging.getLogger("platform.einvoicing.engine")

MODE_BY_COUNTRY = {
    "JO": "jo_jofotara",
    "SA": "sa_zatca",     # planned — raises NotImplementedError for now
    "AE": "ae_peppol",    # planned
}


@dataclass
class SellerProfile:
    tin: str
    name: str
    city: str = ""
    street: str = ""
    activity_code: str = ""


@dataclass
class EInvoiceResult:
    mode: str
    uuid: str
    icv: int
    pih: str
    invoice_hash: str
    status: str
    provider_reference: str = ""
    qr: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("cleared", "reported", "submitted")


def mode_for_country(country_code: str) -> str | None:
    return MODE_BY_COUNTRY.get((country_code or "").upper())


def clear_invoice(
    *,
    tenant_id,
    scope: str,
    country_code: str,
    number: str,
    issue_dt: datetime,
    currency: str,
    seller: SellerProfile,
    buyer_tin: str,
    buyer_name: str,
    buyer_city: str,
    lines: list[dict],
    client: JoFotaraClient | None = None,
) -> EInvoiceResult:
    """Clear one invoice. `lines`: [{name, quantity, unit_price, tax_percent}]."""
    mode = mode_for_country(country_code)
    if mode is None:
        raise ValueError(f"no e-invoicing mode configured for country {country_code!r}")
    if mode != "jo_jofotara":
        raise NotImplementedError(f"e-invoicing mode {mode!r} not implemented yet (see spec §7)")

    uuid_val = str(uuid4())

    with transaction.atomic():
        seq, _ = EInvoiceSequence.objects.select_for_update().get_or_create(
            tenant_id=tenant_id, scope=scope, mode=mode,
        )
        icv = seq.next_icv
        pih = seq.last_hash

        data = JoInvoiceData(
            number=number,
            uuid=uuid_val,
            issue_dt=issue_dt,
            currency=currency,
            icv=icv,
            pih=pih,
            seller=UblParty(tin=seller.tin, name=seller.name, country_code="JO",
                            city=seller.city, street=seller.street),
            buyer=UblParty(tin=buyer_tin, name=buyer_name or "General Public",
                           country_code="JO", city=buyer_city),
            lines=[
                UblLine(
                    line_id=str(i + 1),
                    name=ln["name"],
                    quantity=Decimal(str(ln["quantity"])),
                    unit_price=Decimal(str(ln["unit_price"])),
                    tax_percent=Decimal(str(ln.get("tax_percent", 0))),
                )
                for i, ln in enumerate(lines)
            ],
        )
        xml = build_jo_ubl(data)
        # Hash the canonical UNSIGNED document for the PIH chain (stable across
        # re-signing); submit the signed document.
        this_hash = invoice_hash(xml)
        signed_xml = get_signer(mode).sign(xml)

        interaction = EInvoiceInteraction.objects.create(
            tenant_id=tenant_id, mode=mode, invoice_ref=number, invoice_uuid=uuid_val,
            icv=icv, pih=pih, invoice_hash=this_hash, status="pending",
            request_xml_sha=_sha_hex(xml),
        )

        result = EInvoiceResult(mode=mode, uuid=uuid_val, icv=icv, pih=pih,
                                invoice_hash=this_hash, status="pending")
        cli = client or JoFotaraClient()
        try:
            resp = cli.submit_invoice(signed_xml, uuid_val)
            result.status = "cleared" if resp["status"] in ("cleared", "submitted") else resp["status"]
            result.provider_reference = resp["reference"]
            result.qr = resp.get("qr", "")
            interaction.status = result.status
            interaction.provider_reference = result.provider_reference
            interaction.qr = result.qr
            interaction.response = resp["raw"]
        except Exception as exc:                     # transport / HTTP / value errors
            logger.warning("jofotara clearance failed for %s: %s", number, exc)
            result.status = "rejected"
            result.error = str(exc)
            interaction.status = "rejected"
            interaction.error_message = str(exc)

        interaction.save(update_fields=[
            "status", "provider_reference", "qr", "response", "error_message", "updated_at",
        ])

        # advance the chain only on a real acceptance; a rejection keeps the ICV
        # so the next attempt reuses it (JoFotara is idempotent on invoiceUuid...
        # a fresh attempt gets a fresh uuid but the same ICV slot).
        if result.ok:
            seq.next_icv = icv + 1
            seq.last_hash = this_hash
            seq.save(update_fields=["next_icv", "last_hash", "updated_at"])

    return result


def _sha_hex(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
