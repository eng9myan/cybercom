"""
UBL 2.1 invoice builders, one per e-invoicing mode.

`build_jo_ubl` produces a JoFotara PINT-JO income tax invoice (type 388).
The document shape follows the ISTD PINT-JO specification: supplier/customer
parties by TIN, per-rate tax subtotals, per-line detail, ICV + PIH document
references, and a LegalMonetaryTotal that ties to the lines.

Full XSD + Schematron conformance is validated during ISTD sandbox onboarding
(see docs/blueprint/specs/einvoicing-clearance-engine.md §4.1); this builder
gets the structure and the arithmetic right so that step is a review, not a
rebuild.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

_NS = {
    "": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
}
for _p, _u in _NS.items():
    ET.register_namespace(_p, _u)


def _q(tag: str) -> str:
    prefix, _, local = tag.partition(":")
    if not local:
        return f"{{{_NS['']}}}{prefix}"
    return f"{{{_NS[prefix]}}}{local}"


def _sub(parent: ET.Element, tag: str, text: str | None = None, **attrs) -> ET.Element:
    el = ET.SubElement(parent, _q(tag), {k.replace("_", ""): str(v) for k, v in attrs.items()})
    if text is not None:
        el.text = str(text)
    return el


def _money(v) -> str:
    return str(Decimal(str(v)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


@dataclass
class UblParty:
    tin: str
    name: str
    country_code: str = "JO"
    city: str = ""
    street: str = ""


@dataclass
class UblLine:
    line_id: str
    name: str
    quantity: Decimal
    unit_price: Decimal          # net of line discount, per unit
    tax_percent: Decimal
    unit_code: str = "PCE"

    @property
    def line_extension(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.001"), ROUND_HALF_UP)

    @property
    def tax_amount(self) -> Decimal:
        return (self.line_extension * self.tax_percent / 100).quantize(Decimal("0.001"), ROUND_HALF_UP)


@dataclass
class JoInvoiceData:
    number: str
    uuid: str
    issue_dt: datetime
    currency: str
    icv: int                      # invoice counter value (1-based, per sequence)
    pih: str                      # previous invoice hash (base64) or genesis
    seller: UblParty
    buyer: UblParty
    lines: list[UblLine] = field(default_factory=list)
    invoice_type_code: str = "388"     # 388 tax invoice; 381 credit note

    # ---- totals derived from lines ----
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
        """rate -> (taxable_amount, tax_amount)"""
        out: dict[Decimal, list[Decimal]] = {}
        for l in self.lines:
            slot = out.setdefault(l.tax_percent, [Decimal("0"), Decimal("0")])
            slot[0] += l.line_extension
            slot[1] += l.tax_amount
        return {r: (a, t) for r, (a, t) in out.items()}


def build_jo_ubl(data: JoInvoiceData) -> str:
    """Return a PINT-JO UBL 2.1 Invoice document as a unicode XML string."""
    root = ET.Element(_q("Invoice"))

    _sub(root, "cbc:ProfileID", "reporting:1.0")
    _sub(root, "cbc:ID", data.number)
    _sub(root, "cbc:UUID", data.uuid)
    _sub(root, "cbc:IssueDate", data.issue_dt.date().isoformat())
    _sub(root, "cbc:IssueTime", data.issue_dt.time().replace(microsecond=0).isoformat())
    _sub(root, "cbc:InvoiceTypeCode", data.invoice_type_code, name="011")  # 011: sale, cash
    _sub(root, "cbc:DocumentCurrencyCode", data.currency)
    _sub(root, "cbc:TaxCurrencyCode", "JOD")

    icv_ref = _sub(root, "cac:AdditionalDocumentReference")
    _sub(icv_ref, "cbc:ID", "ICV")
    _sub(icv_ref, "cbc:UUID", str(data.icv))

    pih_ref = _sub(root, "cac:AdditionalDocumentReference")
    _sub(pih_ref, "cbc:ID", "PIH")
    att = _sub(pih_ref, "cac:Attachment")
    _sub(att, "cbc:EmbeddedDocumentBinaryObject", data.pih, mimeCode="text/plain")

    _party(root, "cac:AccountingSupplierParty", data.seller)
    _party(root, "cac:AccountingCustomerParty", data.buyer)

    # document-level TaxTotal with a TaxSubtotal per rate
    tax_total_el = _sub(root, "cac:TaxTotal")
    _sub(tax_total_el, "cbc:TaxAmount", _money(data.tax_total), currencyID=data.currency)
    for rate, (taxable, tax) in sorted(data.tax_subtotals().items()):
        st = _sub(tax_total_el, "cac:TaxSubtotal")
        _sub(st, "cbc:TaxableAmount", _money(taxable), currencyID=data.currency)
        _sub(st, "cbc:TaxAmount", _money(tax), currencyID=data.currency)
        cat = _sub(st, "cac:TaxCategory")
        _sub(cat, "cbc:ID", "S" if rate > 0 else "Z")
        _sub(cat, "cbc:Percent", str(Decimal(str(rate))))
        scheme = _sub(cat, "cac:TaxScheme")
        _sub(scheme, "cbc:ID", "VAT")

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
        itc = _sub(item, "cac:ClassifiedTaxCategory")
        _sub(itc, "cbc:ID", "S" if line.tax_percent > 0 else "Z")
        _sub(itc, "cbc:Percent", str(Decimal(str(line.tax_percent))))
        its = _sub(itc, "cac:TaxScheme")
        _sub(its, "cbc:ID", "VAT")
        price = _sub(il, "cac:Price")
        _sub(price, "cbc:PriceAmount", _money(line.unit_price), currencyID=data.currency)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _party(parent: ET.Element, wrapper_tag: str, p: UblParty) -> None:
    w = _sub(parent, wrapper_tag)
    party = _sub(w, "cac:Party")
    pts = _sub(party, "cac:PartyTaxScheme")
    _sub(pts, "cbc:CompanyID", p.tin or "0")
    scheme = _sub(pts, "cac:TaxScheme")
    _sub(scheme, "cbc:ID", "VAT" if p.tin else "TOT")
    ent = _sub(party, "cac:PartyLegalEntity")
    _sub(ent, "cbc:RegistrationName", p.name)
    addr = _sub(party, "cac:PostalAddress")
    if p.street:
        _sub(addr, "cbc:StreetName", p.street)
    if p.city:
        _sub(addr, "cbc:CityName", p.city)
    country = _sub(addr, "cac:Country")
    _sub(country, "cbc:IdentificationCode", p.country_code)
