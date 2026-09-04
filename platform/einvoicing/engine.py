"""
E-invoicing clearance orchestration.

`clear_invoice(...)` — the one entry point product code calls after an invoice
is finalised:

    1. resolve the mode from the tenant's country (jo_jofotara | sa_zatca | ...)
    2. lock the (tenant, scope) sequence row, take the next ICV + the PIH
    3. build + sign the UBL 2.1 document for that mode
    4. compute the invoice hash (canonical unsigned), for the PIH chain
    5. submit to the authority (JoFotara / ZATCA / Peppol AP)
    6. persist the result + write an EInvoiceInteraction
    7. advance the sequence only on a real acceptance

For JO the call is non-blocking by policy (a rejection sets einvoice_status
"rejected", never rolls back the GL entry). For SA standard (B2B) invoices the
document is not valid to send until ZATCA clears it — the caller must check
`result.ok` before delivering the invoice to the customer.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from django.db import transaction

from .clients.jofotara import JoFotaraClient
from .hashing import invoice_hash
from .models import EInvoiceInteraction, EInvoiceSequence
from .signing import get_signer
from .ubl import JoInvoiceData, UblLine, UblParty, build_jo_ubl

logger = logging.getLogger("platform.einvoicing.engine")

MODE_BY_COUNTRY = {"JO": "jo_jofotara", "SA": "sa_zatca", "AE": "ae_peppol"}
_IMPLEMENTED = {"jo_jofotara", "sa_zatca"}


@dataclass
class SellerProfile:
    tin: str            # JoFotara TIN or ZATCA VAT number
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


def _mk_lines(lines: list[dict]) -> list[UblLine]:
    return [
        UblLine(
            line_id=str(i + 1),
            name=ln["name"],
            quantity=Decimal(str(ln["quantity"])),
            unit_price=Decimal(str(ln["unit_price"])),
            tax_percent=Decimal(str(ln.get("tax_percent", 0))),
        )
        for i, ln in enumerate(lines)
    ]


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
    is_simplified: bool = False,       # SA: True => B2C reporting; False => B2B clearance
    client=None,
) -> EInvoiceResult:
    """Clear one invoice. `lines`: [{name, quantity, unit_price, tax_percent}]."""
    mode = mode_for_country(country_code)
    if mode is None:
        raise ValueError(f"no e-invoicing mode configured for country {country_code!r}")
    if mode not in _IMPLEMENTED:
        raise NotImplementedError(f"e-invoicing mode {mode!r} not implemented yet (see spec §7)")

    uuid_val = str(uuid4())

    with transaction.atomic():
        seq, _ = EInvoiceSequence.objects.select_for_update().get_or_create(
            tenant_id=tenant_id, scope=scope, mode=mode,
        )
        icv, pih = seq.next_icv, seq.last_hash

        if mode == "jo_jofotara":
            xml, submit = _build_jo(
                number, uuid_val, issue_dt, currency, icv, pih,
                seller, buyer_tin, buyer_name, buyer_city, lines, client, mode,
            )
        else:  # sa_zatca
            xml, submit = _build_sa(
                number, uuid_val, issue_dt, currency, icv, pih,
                seller, buyer_tin, buyer_name, buyer_city, lines, is_simplified, client,
            )

        this_hash = invoice_hash(xml)

        interaction = EInvoiceInteraction.objects.create(
            tenant_id=tenant_id, mode=mode, invoice_ref=number, invoice_uuid=uuid_val,
            icv=icv, pih=pih, invoice_hash=this_hash, status="pending",
            request_xml_sha=hashlib.sha256(xml.encode()).hexdigest(),
        )
        result = EInvoiceResult(mode=mode, uuid=uuid_val, icv=icv, pih=pih,
                                invoice_hash=this_hash, status="pending")
        try:
            resp = submit()
            result.status = _norm_status(resp["status"])
            result.provider_reference = resp.get("reference", "")
            result.qr = resp.get("qr", "")
            interaction.status = result.status
            interaction.provider_reference = result.provider_reference
            interaction.qr = result.qr
            interaction.response = resp.get("raw", {})
        except Exception as exc:
            logger.warning("%s clearance failed for %s: %s", mode, number, exc)
            result.status, result.error = "rejected", str(exc)
            interaction.status, interaction.error_message = "rejected", str(exc)

        interaction.save(update_fields=[
            "status", "provider_reference", "qr", "response", "error_message", "updated_at",
        ])

        if result.ok:
            seq.next_icv = icv + 1
            seq.last_hash = this_hash
            seq.save(update_fields=["next_icv", "last_hash", "updated_at"])

    return result


def _norm_status(s: str) -> str:
    return "cleared" if s in ("cleared", "submitted") else s


# ── JO ─────────────────────────────────────────────────────────────────────
def _build_jo(number, uuid_val, issue_dt, currency, icv, pih,
              seller, buyer_tin, buyer_name, buyer_city, lines, client, mode):
    data = JoInvoiceData(
        number=number, uuid=uuid_val, issue_dt=issue_dt, currency=currency, icv=icv, pih=pih,
        seller=UblParty(tin=seller.tin, name=seller.name, country_code="JO",
                        city=seller.city, street=seller.street),
        buyer=UblParty(tin=buyer_tin, name=buyer_name or "General Public",
                       country_code="JO", city=buyer_city),
        lines=_mk_lines(lines),
    )
    xml = build_jo_ubl(data)
    signed = get_signer(mode).sign(xml)
    cli = client or JoFotaraClient()

    def submit():
        return cli.submit_invoice(signed, uuid_val)

    return xml, submit


# ── SA ─────────────────────────────────────────────────────────────────────
def _build_sa(number, uuid_val, issue_dt, currency, icv, pih,
              seller, buyer_tin, buyer_name, buyer_city, lines, is_simplified, client):
    import base64

    from .sa.client import ZatcaClient
    from .sa.qr import encode_qr
    from .sa.signing import ZatcaSigner, canonical_hash
    from .sa.ubl import SaInvoiceData, build_sa_ubl
    from .signing import KEY_LOADER

    data = SaInvoiceData(
        number=number, uuid=uuid_val, issue_dt=issue_dt, currency=currency, icv=icv, pih=pih,
        seller=UblParty(tin=seller.tin, name=seller.name, country_code="SA",
                        city=seller.city, street=seller.street),
        seller_vat=seller.tin,
        buyer=UblParty(tin=buyer_tin, name=buyer_name or "", country_code="SA", city=buyer_city),
        buyer_vat=buyer_tin,
        lines=_mk_lines(lines),
        is_simplified=is_simplified,
    )
    xml = build_sa_ubl(data)

    key_pem, cert_pem = KEY_LOADER("sa_zatca")
    if key_pem and cert_pem:
        parts = ZatcaSigner(key_pem, cert_pem).sign_hash(xml)
    else:
        logger.warning("ZATCA CSID key not configured — QR carries tags 1-5 only, no stamp")
        parts = {"invoice_hash": canonical_hash(xml), "signature": "", "public_key": ""}

    _2dp = Decimal("0.01")
    qr = encode_qr(
        seller_name=seller.name, seller_vat=seller.tin,
        timestamp_iso=issue_dt.replace(microsecond=0).isoformat(),
        invoice_total=str(data.tax_inclusive_total.quantize(_2dp)),
        vat_total=str(data.tax_total.quantize(_2dp)),
        xml_hash_b64=parts["invoice_hash"], signature_b64=parts["signature"],
        public_key_der_b64=parts["public_key"],
    )
    invoice_b64 = base64.b64encode(xml.encode("utf-8")).decode("ascii")
    cli = client or ZatcaClient()

    def submit():
        resp = cli.submit(
            is_simplified=is_simplified, invoice_hash_b64=parts["invoice_hash"],
            uuid=uuid_val, invoice_b64=invoice_b64,
        )
        # for simplified invoices ZATCA doesn't return a QR — we embed our own
        resp.setdefault("qr", "")
        if not resp["qr"]:
            resp["qr"] = qr
        return resp

    return xml, submit
