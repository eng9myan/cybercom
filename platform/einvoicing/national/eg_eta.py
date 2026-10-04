"""
Egypt -- ETA (Egyptian Tax Authority) e-invoice, Invoice v1.0 JSON schema,
submitted directly to the ETA e-invoicing API (no intermediary, like
JoFotara/ZATCA).

Field names/casing/nesting are taken verbatim from the published sample on
sdk.invoicing.eta.gov.eg/documents/invoice-v1-0/ (see schemas/eg/$comment
for why the full official JSON Schema file itself isn't vendored -- it's
only handed out via the preprod sandbox). Scope: the domestic Invoice v1.0
document only. ETA covers exports through a *separate* "Export Invoice
v1.0" schema with its own fields (incoterm, export port, etc.) -- not built
here; a non-Egypt buyer is reported `not_applicable` rather than guessed at.

Signing: ETA requires a CAdES-BES detached signature (PKCS#7 SignedData)
over a specific whitespace-free, uppercase-property-name canonical
serialization of the document (see `canonical_serialize` below, built from
ETA's own "Document Serialization Approach" page) -- NOT the raw JSON
bytes. In production the taxpayer's own USB-token/HSM certificate produces
this; here `sign()` builds a real PKCS#7 signature via `cryptography` from
whatever key/cert `ETA_PRIVATE_KEY_PATH`/`ETA_CERT_PATH` point at (same
seam as every other format's `KEY_LOADER`), and fails honestly
(`TransportNotConfigured`) with nothing configured -- it never fakes a
signed document.
"""
from __future__ import annotations

import base64
import json
import re
from datetime import timezone
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

from .base import (
    SCHEMAS_DIR,
    DocInput,
    EInvoiceDataMissing,
    FieldSpec,
    NationalFormat,
    PartyInput,
    TransportNotConfigured,
    resolve_line_value,
)

TRN_RE = r"[0-9]{9}"
_RATES = {Decimal(x) for x in ("0", "5", "10", "14")}  # 14% is the standard EG VAT rate; 0/5/10 cover reduced goods

_is_eg = lambda doc, p: (p.country_code or "EG").upper() == "EG"  # noqa: E731


def _addr(party: PartyInput) -> dict:
    return {
        "country": (party.country_code or "EG").upper(),
        "governate": party.get("governate") or party.region or "",
        "regionCity": party.city or "",
        "street": party.street or "",
        "buildingNumber": party.building_number or "",
        "postalCode": party.postal_code or "",
    }


def _party(party: PartyInput, *, allow_anonymous: bool) -> dict:
    tax_id = (party.tax_id or "").strip()
    out = {
        "type": "B" if tax_id else "P",
        "id": tax_id or ("0" if allow_anonymous else ""),
        "name": party.name or "",
        "address": _addr(party),
    }
    return out


class EgEta(NationalFormat):
    mode = "eg_eta"
    label = "Egypt - ETA e-invoice (Invoice v1.0)"
    countries = ("EG",)
    content_type = "application/json"
    fields = [
        FieldSpec("seller", "tax_id", "TRN (Tax Registration Number)", pattern=TRN_RE),
        FieldSpec("seller", "name", "Legal / registration name"),
        FieldSpec("seller", "street", "Street"),
        FieldSpec("seller", "city", "City / region"),
        FieldSpec("seller", "activity_code", "Taxpayer activity code (ETA classification)"),
        FieldSpec("buyer", "name", "Legal name"),
        FieldSpec("buyer", "tax_id", "TRN", required=False, pattern=TRN_RE,
                  help="Leave blank for an anonymous B2C receiver."),
        FieldSpec("line", "item_code", "Item code (GS1 GPC or internal EGS code)"),
        FieldSpec("line", "item_type", "Item code system", required=False,
                  choices=(("EGS", "Egypt internal code"), ("GS1", "GS1 GPC")), default_from="default_item_type"),
        FieldSpec("seller", "default_item_type", "Item code system (default)", required=False,
                  choices=(("EGS", "Egypt internal code"), ("GS1", "GS1 GPC"))),
        FieldSpec("line", "unit_type", "Unit of measure (UN/ECE Rec 20 code, e.g. PCE, KGM)"),
        FieldSpec("line", "tax_subtype", "VAT subtype", required=False,
                  choices=(("V009", "General item sales (standard rate)"), ("V003", "Exempt"), ("V001", "Export")),
                  help="Defaults to V009 for a taxed line, V003 for a zero-rated one."),
        FieldSpec("document", "currency_exchange_rate", "Exchange rate to EGP",
                  when=lambda doc, _: doc.currency.upper() != "EGP"),
    ]

    def not_applicable_reason(self, doc: DocInput) -> str | None:
        if not _is_eg(doc, doc.buyer):
            return ("ETA Invoice v1.0 covers domestic (Egypt) sales only; a non-Egypt buyer needs the "
                    "separate Export Invoice v1.0 document, which this engine does not build yet.")
        return None

    def validate(self, doc: DocInput) -> None:
        problems: list[dict] = []
        try:
            super().validate(doc)
        except EInvoiceDataMissing as exc:
            problems = exc.problems
        for i, line in enumerate(doc.lines, start=1):
            if Decimal(line.tax_percent).normalize() not in _RATES:
                problems.append({"scope": f"line[{i}]", "key": "tax_percent", "label": "VAT rate",
                                 "message": f"{line.tax_percent}% is not an Egyptian VAT rate (0 / 5 / 10 / 14)"})
        if doc.is_credit_note and not doc.original_number:
            problems.append({"scope": "document", "key": "original_number", "label": "Original invoice",
                             "message": "a credit note must reference the original invoice's UUID "
                                        "(only known once ETA has cleared it)"})
        if problems:
            raise EInvoiceDataMissing(self.mode, problems)

    def signing_status(self) -> bool:
        try:
            _signing_key()
            return True
        except TransportNotConfigured:
            return False

    def signing_problems(self, doc: DocInput) -> list[dict]:
        try:
            _signing_key()
        except TransportNotConfigured as exc:
            return [{"scope": "seller", "key": "certificate", "label": "Signing certificate (USB token / HSM)",
                     "message": str(exc)}]
        return []

    def build(self, doc: DocInput) -> str:
        self.validate(doc)
        currency = doc.currency.upper()
        fx_rate = Decimal(str(doc.get("currency_exchange_rate") or "1")) if currency != "EGP" else Decimal("1")

        lines = []
        sales_total = Decimal("0")
        discount_total = Decimal("0")
        net_total = Decimal("0")
        tax_by_type: dict[str, Decimal] = {}

        for i, line in enumerate(doc.lines, start=1):
            rate = Decimal(line.tax_percent)
            qty = Decimal(line.quantity)
            unit_price = Decimal(line.unit_price)
            sales = (qty * unit_price).quantize(Decimal("0.00001"), ROUND_HALF_UP)
            tax = (sales * rate / 100).quantize(Decimal("0.00001"), ROUND_HALF_UP)
            amount_egp = (unit_price * fx_rate).quantize(Decimal("0.00001"), ROUND_HALF_UP)

            subtype = resolve_line_value(next(f for f in self.fields if f.key == "tax_subtype"), doc, line)
            subtype = subtype or ("V009" if rate > 0 else "V003")
            item_type = resolve_line_value(next(f for f in self.fields if f.key == "item_type"), doc, line) or "EGS"
            item_code = resolve_line_value(next(f for f in self.fields if f.key == "item_code"), doc, line)
            unit_type = resolve_line_value(next(f for f in self.fields if f.key == "unit_type"), doc, line)

            lines.append({
                "description": _txt(line.name, 500),
                "itemType": item_type,
                "itemCode": str(item_code),
                "unitType": unit_type,
                "quantity": _num(qty, 5),
                "unitValue": {
                    "currencySold": currency,
                    "amountEGP": _num(amount_egp, 5),
                    "amountSold": _num(unit_price, 5),
                    "currencyExchangeRate": _num(fx_rate, 5),
                },
                "salesTotal": _num(sales, 5),
                "total": _num(sales + tax, 5),
                "netTotal": _num(sales, 5),
                "taxableItems": [
                    {"taxType": "T1", "amount": _num(tax, 5), "subType": subtype, "rate": _num(rate, 2)},
                ],
                "internalCode": str(i),
            })
            sales_total += sales
            net_total += sales
            tax_by_type["T1"] = tax_by_type.get("T1", Decimal("0")) + tax

        total_amount = net_total + sum(tax_by_type.values())

        document: dict = {
            "issuer": _party(doc.seller, allow_anonymous=False),
            "receiver": _party(doc.buyer, allow_anonymous=True),
            "documentType": "c" if doc.is_credit_note else "i",
            "documentTypeVersion": "1.0",
            "dateTimeIssued": doc.issue_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "taxpayerActivityCode": str(doc.seller.get("activity_code") or ""),
            "internalId": doc.number,
            "invoiceLines": lines,
            "totalSalesAmount": _num(sales_total, 5),
            "totalDiscountAmount": _num(discount_total, 5),
            "netAmount": _num(net_total, 5),
            "taxTotals": [{"taxType": t, "amount": _num(a, 5)} for t, a in tax_by_type.items()],
            "totalAmount": _num(total_amount, 5),
        }
        if doc.is_credit_note and doc.original_number:
            document["references"] = [{"uuid": doc.original_number}]
        return json.dumps({"document": document}, ensure_ascii=False)

    def schema_errors(self, document: str) -> list[str]:
        import jsonschema

        try:
            payload = json.loads(document)
        except json.JSONDecodeError as exc:
            return [f"not valid JSON: {exc}"]
        return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
                for e in _validator().iter_errors(payload)]

    def sign(self, document: str, doc: DocInput) -> str:
        key, cert = _signing_key()
        canonical = canonical_serialize(json.loads(document)["document"])
        signature = _pkcs7_detached_sign(canonical.encode("utf-8"), key, cert)
        payload = json.loads(document)
        payload["document"]["signatures"] = [{"type": "I", "value": base64.b64encode(signature).decode("ascii")}]
        return json.dumps(payload, ensure_ascii=False)

    def filename(self, doc: DocInput) -> str:
        return f"ETA_{doc.seller.tax_id}_{re.sub(r'[^A-Za-z0-9-]', '_', doc.number)}.json"

    def submit(self, signed: str, doc: DocInput, client=None) -> dict:
        return (client or self.client()).submit_document(signed, internal_id=doc.number)

    def client(self):
        from ..clients.eta import EtaClient

        c = EtaClient()
        if not c.is_configured():
            raise TransportNotConfigured(
                "No ETA transport configured. Set ETA_CLIENT_ID and ETA_CLIENT_SECRET (from the taxpayer's "
                "ERP/POS onboarding on the ETA preprod/production portal) to transmit; the signed document "
                "itself is generated and stored and can be filed manually before that account exists."
            )
        return c


def canonical_serialize(value, prop_name: str | None = None) -> str:
    """ETA's own canonicalization for computing the signed hash: every
    property name is uppercased and every (name, value) pair is pure string
    concatenation with no separators; an array repeats "NAME" before each
    element instead of using brackets/commas. Values are taken as the exact
    string already in the document (so numeric formatting here MUST match
    what `build()` wrote, which `_num` guarantees)."""
    if isinstance(value, dict):
        out = f'"{prop_name.upper()}"' if prop_name else ""
        for k, v in value.items():
            out += canonical_serialize(v, k)
        return out
    if isinstance(value, list):
        # ETA's own example: "TAXABLEITEMS""TAXABLEITEMS"<item1>"TAXABLEITEMS"<item2>...
        # -- the array's own name label, then name+item repeated per element.
        name = f'"{prop_name.upper()}"' if prop_name else ""
        out = name
        for item in value:
            out += name
            out += canonical_serialize(item)
        return out
    # simple scalar
    out = f'"{prop_name.upper()}"' if prop_name else ""
    out += f'"{value}"'
    return out


def _pkcs7_detached_sign(data: bytes, key, cert) -> bytes:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.serialization import pkcs7

    return (
        pkcs7.PKCS7SignatureBuilder()
        .set_data(data)
        .add_signer(cert, key, hashes.SHA256())
        .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
    )


def _signing_key():
    import os

    from cryptography.x509 import load_der_x509_certificate, load_pem_x509_certificate
    from cryptography.hazmat.primitives.serialization import load_der_private_key, load_pem_private_key

    from ..signing import KEY_LOADER

    key_bytes, cert_bytes = KEY_LOADER("eg_eta")
    if not key_bytes or not cert_bytes:
        raise TransportNotConfigured(
            "No signing certificate installed. Set ETA_PRIVATE_KEY_PATH and ETA_CERT_PATH (the taxpayer's "
            "own USB-token-issued or HSM-backed key/cert) and ETA_KEY_PASSWORD if the key is encrypted."
        )
    password = os.getenv("ETA_KEY_PASSWORD", "").encode() or None
    try:
        key = (load_pem_private_key(key_bytes, password) if b"-----BEGIN" in key_bytes
               else load_der_private_key(key_bytes, password))
        cert = (load_pem_x509_certificate(cert_bytes) if b"-----BEGIN" in cert_bytes
                else load_der_x509_certificate(cert_bytes))
    except Exception as exc:
        raise TransportNotConfigured(f"Could not load the configured ETA signing certificate: {exc}") from exc
    return key, cert


@lru_cache(maxsize=1)
def _validator():
    import jsonschema

    schema = json.loads((SCHEMAS_DIR / "eg" / "eta_invoice_v1.0.schema.json").read_text(encoding="utf-8"))
    return jsonschema.Draft7Validator(schema)


def _txt(value, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _num(value: Decimal, places: int) -> float:
    q = Decimal(1).scaleb(-places)
    return float(Decimal(value).quantize(q, rounding=ROUND_HALF_UP))
