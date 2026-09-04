"""
ZATCA (KSA) UBL 2.1 invoice builder.

Shares the line/party value objects with `platform.einvoicing.ubl`; the
document shape follows ZATCA's `reporting:1.0` / `clearance` profile:
seller VAT + address + party identification, buyer, per-rate TaxSubtotal with
category codes, per-line detail, and the ICV / PIH / QR AdditionalDocument
References. The `<ext:UBLExtensions>` signature block is added during ZATCA
compliance onboarding (their conformance suite validates the exact shape).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from platform.einvoicing.ubl import UblLine, UblParty, _NS, _q, _sub, _money

# 388 standard tax invoice, 381 credit note, 383 debit note
INVOICE_TYPE_STANDARD = "388"
# subtype: 0100000 standard (B2B), 0200000 simplified (B2C)
SUBTYPE_STANDARD = "0100000"
SUBTYPE_SIMPLIFIED = "0200000"


@dataclass
class SaInvoiceData:
    number: str
    uuid: str
    issue_dt: datetime
    currency: str
    icv: int
    pih: str
    seller: UblParty
    seller_vat: str
    buyer: UblParty
    buyer_vat: str
    lines: list[UblLine] = field(default_factory=list)
    invoice_type_code: str = INVOICE_TYPE_STANDARD
    is_simplified: bool = False

    @property
    def subtype(self) -> str:
        return SUBTYPE_SIMPLIFIED if self.is_simplified else SUBTYPE_STANDARD

    @property
    def line_extension_total(self) -> Decimal:
        return sum((l.line_extension for l in self.lines), Decimal("0"))

    @property
    def tax_total(self) -> Decimal:
        return sum((l.tax_amount for l in self.lines), Decimal("0"))

    @property
    def tax_inclusive_total(self) -> Decimal:
        return self.line_extension_total + self.tax_total

    def tax_subtotals(self) -> dict[Decimal, tuple[Decimal, Decimal]]:
        out: dict[Decimal, list[Decimal]] = {}
        for l in self.lines:
            slot = out.setdefault(l.tax_percent, [Decimal("0"), Decimal("0")])
            slot[0] += l.line_extension
            slot[1] += l.tax_amount
        return {r: (a, t) for r, (a, t) in out.items()}


def build_sa_ubl(data: SaInvoiceData) -> str:
    root = ET.Element(_q("Invoice"))

    _sub(root, "cbc:ProfileID", "reporting:1.0")
    _sub(root, "cbc:ID", data.number)
    _sub(root, "cbc:UUID", data.uuid)
    _sub(root, "cbc:IssueDate", data.issue_dt.date().isoformat())
    _sub(root, "cbc:IssueTime", data.issue_dt.time().replace(microsecond=0).isoformat())
    itc = _sub(root, "cbc:InvoiceTypeCode", data.invoice_type_code)
    itc.set("name", data.subtype)
    _sub(root, "cbc:DocumentCurrencyCode", data.currency)
    _sub(root, "cbc:TaxCurrencyCode", "SAR")

    icv_ref = _sub(root, "cac:AdditionalDocumentReference")
    _sub(icv_ref, "cbc:ID", "ICV")
    _sub(icv_ref, "cbc:UUID", str(data.icv))

    pih_ref = _sub(root, "cac:AdditionalDocumentReference")
    _sub(pih_ref, "cbc:ID", "PIH")
    att = _sub(pih_ref, "cac:Attachment")
    _sub(att, "cbc:EmbeddedDocumentBinaryObject", data.pih, mimeCode="text/plain")

    _sa_party(root, "cac:AccountingSupplierParty", data.seller, data.seller_vat)
    _sa_party(root, "cac:AccountingCustomerParty", data.buyer, data.buyer_vat)

    tt = _sub(root, "cac:TaxTotal")
    _sub(tt, "cbc:TaxAmount", _money(data.tax_total), currencyID=data.currency)
    for rate, (taxable, tax) in sorted(data.tax_subtotals().items()):
        st = _sub(tt, "cac:TaxSubtotal")
        _sub(st, "cbc:TaxableAmount", _money(taxable), currencyID=data.currency)
        _sub(st, "cbc:TaxAmount", _money(tax), currencyID=data.currency)
        cat = _sub(st, "cac:TaxCategory")
        _sub(cat, "cbc:ID", "S" if rate > 0 else "Z")
        _sub(cat, "cbc:Percent", str(Decimal(str(rate))))
        sch = _sub(cat, "cac:TaxScheme")
        _sub(sch, "cbc:ID", "VAT")

    lmt = _sub(root, "cac:LegalMonetaryTotal")
    _sub(lmt, "cbc:LineExtensionAmount", _money(data.line_extension_total), currencyID=data.currency)
    _sub(lmt, "cbc:TaxExclusiveAmount", _money(data.line_extension_total), currencyID=data.currency)
    _sub(lmt, "cbc:TaxInclusiveAmount", _money(data.tax_inclusive_total), currencyID=data.currency)
    _sub(lmt, "cbc:PayableAmount", _money(data.tax_inclusive_total), currencyID=data.currency)

    for line in data.lines:
        il = _sub(root, "cac:InvoiceLine")
        _sub(il, "cbc:ID", line.line_id)
        _sub(il, "cbc:InvoicedQuantity", str(line.quantity), unitCode=line.unit_code)
        _sub(il, "cbc:LineExtensionAmount", _money(line.line_extension), currencyID=data.currency)
        lt = _sub(il, "cac:TaxTotal")
        _sub(lt, "cbc:TaxAmount", _money(line.tax_amount), currencyID=data.currency)
        _sub(lt, "cbc:RoundingAmount", _money(line.line_extension + line.tax_amount), currencyID=data.currency)
        item = _sub(il, "cac:Item")
        _sub(item, "cbc:Name", line.name)
        ctc = _sub(item, "cac:ClassifiedTaxCategory")
        _sub(ctc, "cbc:ID", "S" if line.tax_percent > 0 else "Z")
        _sub(ctc, "cbc:Percent", str(Decimal(str(line.tax_percent))))
        cts = _sub(ctc, "cac:TaxScheme")
        _sub(cts, "cbc:ID", "VAT")
        price = _sub(il, "cac:Price")
        _sub(price, "cbc:PriceAmount", _money(line.unit_price), currencyID=data.currency)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _sa_party(parent: ET.Element, wrapper_tag: str, p: UblParty, vat: str) -> None:
    w = _sub(parent, wrapper_tag)
    party = _sub(w, "cac:Party")
    if vat:
        pi = _sub(party, "cac:PartyIdentification")
        _sub(pi, "cbc:ID", vat, schemeID="CRN")
    pts = _sub(party, "cac:PartyTaxScheme")
    _sub(pts, "cbc:CompanyID", vat or "0")
    sch = _sub(pts, "cac:TaxScheme")
    _sub(sch, "cbc:ID", "VAT")
    ent = _sub(party, "cac:PartyLegalEntity")
    _sub(ent, "cbc:RegistrationName", p.name)
    addr = _sub(party, "cac:PostalAddress")
    if p.street:
        _sub(addr, "cbc:StreetName", p.street)
    if p.city:
        _sub(addr, "cbc:CityName", p.city)
    country = _sub(addr, "cac:Country")
    _sub(country, "cbc:IdentificationCode", p.country_code or "SA")
