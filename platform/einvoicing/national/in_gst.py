"""
India -- GST e-invoice (INV-01, schema v1.1) for IRN generation on the
Invoice Registration Portal (IRP), reached through a GSP.

The document is JSON, not XML. It is validated against
schemas/in/irp_einvoice_v1.1.schema.json, which CyCom authored from the NIC
IRP API v1.1 field specification and its published sample request -- see
that file's $comment for why the NIC-hosted file itself isn't vendored.

Rules handled explicitly:
- e-invoicing covers B2B, SEZ and exports only: a domestic sale to a buyer
  without a GSTIN is reported `not_applicable`, not `incomplete`.
- intra-state supply (seller state == place of supply) splits the rate into
  CGST + SGST; inter-state, SEZ and export use IGST. Exports/SEZ at 0% are
  "without payment" (under LUT), otherwise "with payment".
- the seller's state code comes from its own GSTIN; GSTINs are checksum-
  validated (the IRP rejects a bad one).
- a credit note (CRN) references the original invoice number and date.
- the IRN itself, the signed invoice and the QR are produced by the IRP;
  they come back through the GSP (IN_GSP_BASE_URL / IN_GSP_API_KEY) and the
  IRN is recorded as the authority reference.
"""
from __future__ import annotations

import json
import re
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

from .base import (
    SCHEMAS_DIR,
    DocInput,
    EInvoiceDataMissing,
    FieldSpec,
    NationalFormat,
    resolve_line_value,
)
from .transport import IntermediaryClient

GSTIN_RE = r"[0-9]{2}[0-9A-Z]{13}"
DOC_NO_RE = r"[A-Z1-9][A-Z0-9/-]{0,15}"
_RATES = {Decimal(x) for x in ("0", "0.1", "0.25", "1", "1.5", "3", "5", "6", "7.5", "12", "18", "28", "40")}
UQC = tuple((u, u) for u in (
    "BAG", "BOX", "BTL", "CTN", "DOZ", "GMS", "KGS", "KLR", "KME", "LTR", "MTR", "MTS", "NOS",
    "PAC", "PCS", "QTL", "ROL", "SET", "SQF", "SQM", "TON", "UNT", "OTH"))
STATE_CODES = tuple((f"{i:02d}", f"{i:02d}") for i in range(1, 39)) + (("97", "97 Other territory"),)
_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gstin_valid(gstin: str) -> bool:
    g = (gstin or "").strip().upper()
    if not re.fullmatch(GSTIN_RE, g):
        return False
    total = 0
    for i, ch in enumerate(g[:14]):
        product = _CHARS.index(ch) * (2 if i % 2 else 1)
        total += product // 36 + product % 36
    return _CHARS[(36 - total % 36) % 36] == g[14]


_is_in = lambda doc, p: (p.country_code or "").upper() == "IN"  # noqa: E731


def _is_goods(doc, line) -> bool:
    hsn = resolve_line_value(next(f for f in InGst.fields if f.key == "hsn"), doc, line) or ""
    return not str(hsn).startswith("99")  # SAC (services) codes start with 99


class InGst(NationalFormat):
    mode = "in_gst"
    label = "India - GST e-invoice (IRN via IRP)"
    countries = ("IN",)
    content_type = "application/json"
    fields = [
        FieldSpec("seller", "tax_id", "GSTIN", pattern=GSTIN_RE),
        FieldSpec("seller", "name", "Legal name"),
        FieldSpec("seller", "street", "Address line 1"),
        FieldSpec("seller", "city", "Location"),
        FieldSpec("seller", "postal_code", "PIN code", pattern=r"[1-9][0-9]{5}"),
        FieldSpec("seller", "default_hsn", "HSN / SAC (default)", required=False, pattern=r"[0-9]{4}|[0-9]{6}|[0-9]{8}"),
        FieldSpec("seller", "default_unit", "Unit (UQC, default)", required=False, choices=UQC),
        FieldSpec("buyer", "name", "Legal name"),
        FieldSpec("buyer", "country_code", "Country", pattern=r"[A-Z]{2}"),
        FieldSpec("buyer", "street", "Address line 1"),
        FieldSpec("buyer", "city", "Location"),
        FieldSpec("buyer", "postal_code", "PIN code", pattern=r"[1-9][0-9]{5}", when=_is_in),
        FieldSpec("buyer", "sez", "SEZ unit / developer", required=False, choices=(("Y", "Yes"), ("N", "No"))),
        FieldSpec("line", "hsn", "HSN / SAC", pattern=r"[0-9]{4}|[0-9]{6}|[0-9]{8}", default_from="default_hsn"),
        FieldSpec("line", "unit", "Unit (UQC)", choices=UQC, when=_is_goods, default_from="default_unit"),
        FieldSpec("document", "place_of_supply", "Place of supply (state code)", required=False,
                  choices=STATE_CODES, help="Defaults to the buyer's state (from its GSTIN)."),
        FieldSpec("document", "reverse_charge", "Reverse charge", required=False, choices=(("Y", "Yes"), ("N", "No"))),
    ]

    def not_applicable_reason(self, doc: DocInput) -> str | None:
        if _is_in(doc, doc.buyer) and not (doc.buyer.tax_id or "").strip():
            return ("GST e-invoicing (IRN) applies to B2B, SEZ and export supplies only; this is a B2C "
                    "sale to a buyer without a GSTIN.")
        return None

    def validate(self, doc: DocInput) -> None:
        problems: list[dict] = []
        try:
            super().validate(doc)
        except EInvoiceDataMissing as exc:
            problems = exc.problems
        if doc.seller.tax_id and not gstin_valid(doc.seller.tax_id):
            problems.append({"scope": "seller", "key": "tax_id", "label": "GSTIN", "message": "GSTIN checksum is invalid"})
        if _is_in(doc, doc.buyer) and doc.buyer.tax_id and not gstin_valid(doc.buyer.tax_id):
            problems.append({"scope": "buyer", "key": "tax_id", "label": "GSTIN", "message": "GSTIN checksum is invalid"})
        if not re.fullmatch(DOC_NO_RE, doc.number or ""):
            problems.append({"scope": "document", "key": "number", "label": "Document number",
                             "message": "the IRP accepts up to 16 characters A-Z 0-9 / -, not starting with 0 "
                                        "(adjust the invoice numbering sequence prefix)"})
        for i, line in enumerate(doc.lines, start=1):
            if Decimal(line.tax_percent).normalize() not in _RATES:
                problems.append({"scope": f"line[{i}]", "key": "tax_percent", "label": "GST rate",
                                 "message": f"{line.tax_percent}% is not a GST rate"})
        if doc.is_credit_note and not doc.original_number:
            problems.append({"scope": "document", "key": "original_number", "label": "Original invoice",
                             "message": "a credit note must reference the original invoice"})
        if problems:
            raise EInvoiceDataMissing(self.mode, problems)

    def build(self, doc: DocInput) -> str:
        self.validate(doc)
        export = not _is_in(doc, doc.buyer)
        sez = doc.buyer.get("sez") == "Y"
        seller_st = doc.seller.tax_id.strip().upper()[:2]
        buyer_gstin = "URP" if export else doc.buyer.tax_id.strip().upper()
        buyer_st = "96" if export else buyer_gstin[:2]
        pos = "96" if export else (doc.get("place_of_supply") or buyer_st)
        any_tax = any(Decimal(l.tax_percent) > 0 for l in doc.lines)
        if export:
            sup = "EXPWP" if any_tax else "EXPWOP"
        elif sez:
            sup = "SEZWP" if any_tax else "SEZWOP"
        else:
            sup = "B2B"
        intra = sup == "B2B" and seller_st == pos

        items, ass_tot, cgst_tot, sgst_tot, igst_tot = [], Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")
        for i, line in enumerate(doc.lines, start=1):
            rate = Decimal(line.tax_percent)
            ass = line.net
            if intra:
                half = (ass * rate / 200).quantize(Decimal("0.01"), ROUND_HALF_UP)
                cgst, sgst, igst = half, half, Decimal("0")
            else:
                cgst, sgst = Decimal("0"), Decimal("0")
                igst = (ass * rate / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
            ass_tot += ass
            cgst_tot += cgst
            sgst_tot += sgst
            igst_tot += igst
            hsn = resolve_line_value(next(f for f in self.fields if f.key == "hsn"), doc, line)
            goods = not str(hsn).startswith("99")
            item = {
                "SlNo": str(i),
                "PrdDesc": _txt(line.name, 300) or "Item",
                "IsServc": "N" if goods else "Y",
                "HsnCd": str(hsn),
                "Qty": float(Decimal(line.quantity).quantize(Decimal("0.001"))),
                "UnitPrice": float(Decimal(line.unit_price).quantize(Decimal("0.001"))),
                "TotAmt": float(ass),
                "AssAmt": float(ass),
                "GstRt": _rate(rate),
                "IgstAmt": float(igst),
                "CgstAmt": float(cgst),
                "SgstAmt": float(sgst),
                "TotItemVal": float(ass + cgst + sgst + igst),
            }
            if goods:
                item["Unit"] = resolve_line_value(next(f for f in self.fields if f.key == "unit"), doc, line)
            items.append(item)

        seller = {
            "Gstin": doc.seller.tax_id.strip().upper(),
            "LglNm": _txt(doc.seller.name, 100),
            "Addr1": _txt(doc.seller.street, 100),
            "Loc": _txt(doc.seller.city, 100),
            "Pin": int(doc.seller.postal_code),
            "Stcd": seller_st,
        }
        if doc.seller.email:
            seller["Em"] = doc.seller.email[:100]
        buyer = {
            "Gstin": buyer_gstin,
            "LglNm": _txt(doc.buyer.name, 100),
            "Pos": pos,
            "Addr1": _txt(doc.buyer.street, 100),
            "Loc": _txt(doc.buyer.city, 100),
            "Pin": 999999 if export else int(doc.buyer.postal_code),
            "Stcd": buyer_st,
        }
        body = {
            "Version": "1.1",
            "TranDtls": {"TaxSch": "GST", "SupTyp": sup, "RegRev": doc.get("reverse_charge") or "N",
                         "IgstOnIntra": "N"},
            "DocDtls": {"Typ": "CRN" if doc.is_credit_note else "INV", "No": doc.number,
                        "Dt": doc.issue_dt.strftime("%d/%m/%Y")},
            "SellerDtls": seller,
            "BuyerDtls": buyer,
            "ItemList": items,
            "ValDtls": {
                "AssVal": float(ass_tot), "CgstVal": float(cgst_tot), "SgstVal": float(sgst_tot),
                "IgstVal": float(igst_tot), "TotInvVal": float(ass_tot + cgst_tot + sgst_tot + igst_tot),
            },
        }
        if doc.is_credit_note:
            prec = {"InvNo": doc.original_number}
            if doc.original_date:
                prec["InvDt"] = doc.original_date.strftime("%d/%m/%Y")
            body["RefDtls"] = {"PrecDocDtls": [prec]}
        if export:
            body["ExpDtls"] = {"CntCode": doc.buyer.country_code.upper(), "ForCur": doc.currency.upper()}
        return json.dumps(body, ensure_ascii=False, indent=1)

    def schema_errors(self, document: str) -> list[str]:
        import jsonschema

        try:
            payload = json.loads(document)
        except json.JSONDecodeError as exc:
            return [f"not valid JSON: {exc}"]
        return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
                for e in _validator().iter_errors(payload)]

    def filename(self, doc: DocInput) -> str:
        return f"{doc.seller.tax_id.upper()}_{re.sub(r'[^A-Z0-9-]', '_', doc.number)}.json"

    def client(self):
        return IntermediaryClient("IN_GSP", channel_label="GSP (GST Suvidha Provider) for the IRP",
                                  content_type="application/json")


@lru_cache(maxsize=1)
def _validator():
    import jsonschema

    schema = json.loads((SCHEMAS_DIR / "in" / "irp_einvoice_v1.1.schema.json").read_text(encoding="utf-8"))
    return jsonschema.Draft7Validator(schema)


def _txt(value, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _rate(rate: Decimal):
    r = rate.normalize()
    return int(r) if r == r.to_integral_value() else float(r)
