"""
Shared plumbing for national (non-UBL, non-Peppol) e-invoicing formats.

Every national format differs in shape, but they all need the same three
things from the caller, so each format module declares them the same way:

- a normalised input (`DocInput` / `PartyInput` / `LineInput`) that the
  product-side bridge fills from its own models -- the builders never touch
  Django models, so they're testable as pure functions;
- a list of `FieldSpec`s naming every national field the format needs that a
  generic ERP record doesn't carry (Italy's RegimeFiscale, Mexico's
  UsoCFDI, Brazil's NCM, India's HSN, ...). The specs drive BOTH
  `validate()` and the settings UI, so the two can't drift apart;
- an honest failure mode: `EInvoiceDataMissing` lists exactly which fields
  are missing or malformed. A builder never invents a legal code (a tax
  regime, an exemption nature, a product classification) to get a document
  out of the door -- a wrong code is a real compliance error the taxpayer
  answers for, a missing one is a form to fill in.

Transport to each authority/intermediary is a separate, env-configured seam
per format that raises `TransportNotConfigured` rather than faking a
"cleared" -- the same posture as the JoFotara/ZATCA/Peppol clients. The
document itself is always generated and stored, so it can be downloaded and
filed manually before a transport account exists.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Callable

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


class EInvoiceDataMissing(ValueError):
    """The document can't be built without inventing data. `problems` is a
    list of {"scope", "key", "label", "message"} dicts, one per field."""

    def __init__(self, mode: str, problems: list[dict]):
        self.mode = mode
        self.problems = problems
        super().__init__(
            f"{mode}: " + "; ".join(f"{p['scope']}.{p['key']}: {p['message']}" for p in problems)
        )


class TransportNotConfigured(RuntimeError):
    """No transmission channel (authority API / intermediary) configured."""


@dataclass
class PartyInput:
    tax_id: str = ""
    name: str = ""
    street: str = ""
    building_number: str = ""
    city: str = ""
    postal_code: str = ""
    region: str = ""                 # province / state / estado code
    country_code: str = ""
    email: str = ""
    extra: dict[str, Any] = field(default_factory=dict)   # national fields (see FieldSpec)

    def get(self, key: str) -> Any:
        if key in self.__dataclass_fields__ and key != "extra":
            return getattr(self, key)
        return self.extra.get(key)


@dataclass
class LineInput:
    name: str
    quantity: Decimal
    unit_price: Decimal
    tax_percent: Decimal
    extra: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        if key in ("name", "quantity", "unit_price", "tax_percent"):
            return getattr(self, key)
        return self.extra.get(key)

    @property
    def net(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"), ROUND_HALF_UP)

    @property
    def tax(self) -> Decimal:
        return (self.net * self.tax_percent / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)


@dataclass
class DocInput:
    number: str
    issue_dt: datetime
    currency: str
    seller: PartyInput
    buyer: PartyInput
    lines: list[LineInput]
    uuid: str = ""
    icv: int = 1                     # per-sequence counter from EInvoiceSequence
    is_credit_note: bool = False
    original_number: str = ""        # credit note -> the invoice it corrects
    original_date: date | None = None
    due_date: date | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        return self.extra.get(key)

    @property
    def net_total(self) -> Decimal:
        return sum((l.net for l in self.lines), Decimal("0"))

    @property
    def tax_total(self) -> Decimal:
        return sum((l.tax for l in self.lines), Decimal("0"))

    @property
    def gross_total(self) -> Decimal:
        return self.net_total + self.tax_total

    def by_rate(self, key: Callable[[LineInput], Any] | None = None) -> dict:
        """Group lines -> {group_key: (taxable, tax)}; default key is the rate."""
        out: dict = {}
        for l in self.lines:
            k = key(l) if key else l.tax_percent
            taxable, tax = out.get(k, (Decimal("0"), Decimal("0")))
            out[k] = (taxable + l.net, tax + l.tax)
        return out


@dataclass(frozen=True)
class FieldSpec:
    """One national field. `scope` says where the bridge stores it:
    seller -> the tenant's e-invoicing profile, buyer -> the partner,
    line -> the invoice line (or a seller-level default `default_from`),
    document -> the invoice."""

    scope: str                       # seller | buyer | line | document
    key: str
    label: str
    required: bool = True
    pattern: str | None = None       # full-match regex
    choices: tuple[tuple[str, str], ...] = ()
    help: str = ""
    # only required when this predicate on (doc, obj) holds, e.g. IT Natura
    # only for a zero-rated line
    when: Callable[[Any, Any], bool] | None = None
    # line-scope fields may fall back to a seller-profile default key
    default_from: str | None = None

    def as_dict(self) -> dict:
        return {
            "scope": self.scope, "key": self.key, "label": self.label,
            "required": self.required, "pattern": self.pattern,
            "choices": [{"value": v, "label": l} for v, l in self.choices],
            "help": self.help, "conditional": self.when is not None,
            "default_from": self.default_from,
        }


def _check(spec: FieldSpec, value: Any, scope_label: str, problems: list[dict], applies: bool = True):
    empty = value is None or (isinstance(value, str) and not value.strip())
    if empty:
        if spec.required and applies:
            problems.append({"scope": scope_label, "key": spec.key, "label": spec.label, "message": "required"})
        return
    s = str(value).strip()
    if spec.pattern and not re.fullmatch(spec.pattern, s):
        problems.append({"scope": scope_label, "key": spec.key, "label": spec.label,
                         "message": f"'{s}' does not match the required format"})
    if spec.choices and s not in {c for c, _ in spec.choices}:
        problems.append({"scope": scope_label, "key": spec.key, "label": spec.label,
                         "message": f"'{s}' is not a valid option"})


def resolve_line_value(spec: FieldSpec, doc: DocInput, line: LineInput) -> Any:
    value = line.get(spec.key)
    if (value is None or value == "") and spec.default_from:
        value = doc.seller.get(spec.default_from)
    return value


def validate_fields(mode: str, specs: list[FieldSpec], doc: DocInput) -> None:
    """Raise EInvoiceDataMissing listing every problem at once (not just the
    first), so the user fixes the form in one pass."""
    problems: list[dict] = []
    for spec in specs:
        if spec.scope == "seller":
            _check(spec, doc.seller.get(spec.key), "seller", problems,
                   spec.when is None or spec.when(doc, doc.seller))
        elif spec.scope == "buyer":
            _check(spec, doc.buyer.get(spec.key), "buyer", problems,
                   spec.when is None or spec.when(doc, doc.buyer))
        elif spec.scope == "document":
            _check(spec, doc.get(spec.key), "document", problems,
                   spec.when is None or spec.when(doc, doc))
        elif spec.scope == "line":
            for i, line in enumerate(doc.lines, start=1):
                _check(spec, resolve_line_value(spec, doc, line), f"line[{i}]", problems,
                       spec.when is None or spec.when(doc, line))
    if problems:
        raise EInvoiceDataMissing(mode, problems)


def validate_against_xsd(xml: str, xsd_relpath: str) -> list[str]:
    """Validate against a vendored official XSD. Returns error strings
    (empty = valid). Offline: every import is rewritten to a local path."""
    from lxml import etree

    schema = _schema_cache.get(xsd_relpath)
    if schema is None:
        schema = etree.XMLSchema(etree.parse(str(SCHEMAS_DIR / xsd_relpath)))
        _schema_cache[xsd_relpath] = schema
    doc = etree.fromstring(xml.encode("utf-8"))
    if schema.validate(doc):
        return []
    return [f"line {e.line}: {e.message}" for e in schema.error_log]


_schema_cache: dict[str, Any] = {}


def fmt(value: Decimal | int | float | str, places: int) -> str:
    q = Decimal(1).scaleb(-places)
    return str(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))


def ascii_latin(text: str, limit: int) -> str:
    """Trim to a Latin-1 safe string of at most `limit` chars -- several
    national XSDs (FatturaPA's String*LatinType) reject anything outside
    Basic Latin + Latin-1 Supplement."""
    cleaned = "".join(ch if ord(ch) < 256 else "?" for ch in (text or "")).strip()
    return cleaned[:limit]


class NationalFormat:
    """Subclass per format. `build` returns the unsigned document; `sign`
    returns what gets transmitted (identity when the format has no
    document-level signature); `client()` returns the transport seam."""

    mode: str = ""
    label: str = ""
    countries: tuple[str, ...] = ()
    xsd: str | None = None           # relative to SCHEMAS_DIR
    content_type: str = "application/xml"
    fields: list[FieldSpec] = []

    def validate(self, doc: DocInput) -> None:
        validate_fields(self.mode, self.fields, doc)

    def signing_problems(self, doc: DocInput) -> list[dict]:
        """Pre-flight: problems that stop a *legally valid* document being
        produced for lack of signing credentials (e.g. CFDI's CSD, which the
        schema itself requires). Checked before a sequence number is taken."""
        return []

    def build(self, doc: DocInput) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def sign(self, document: str, doc: DocInput) -> str:
        return document

    def filename(self, doc: DocInput) -> str:
        return f"{self.mode}_{re.sub(r'[^A-Za-z0-9_-]', '_', doc.number)}.xml"

    def client(self):  # pragma: no cover - abstract
        raise NotImplementedError

    def submit(self, signed: str, doc: DocInput, client=None) -> dict:
        return (client or self.client()).submit(signed, filename=self.filename(doc), doc=doc)

    def schema_errors(self, document: str) -> list[str]:
        return validate_against_xsd(document, self.xsd) if self.xsd else []
