"""
Poland -- KSeF structured invoice, logical schema FA(3) (mandatory in KSeF
from 2026-02-01), built against the Ministry of Finance XSD vendored under
schemas/pl/ (every builder test schema-validates its output).

Rules the XSD can't express, handled explicitly here:

- VAT is reported per rate *bucket* (P_13_x net / P_14_x tax), with the
  0% cases split by legal basis: domestic 0% ("0 KR"), intra-EU supply
  ("0 WDT"), export ("0 EX"), exempt ("zw"), not taxable in PL ("np I" /
  "np II") and reverse charge ("oo"). A 0% line therefore needs its legal
  basis code -- line value or a seller default, never guessed.
- An exempt ("zw") line needs the exemption's legal basis (P_19A) text.
- A foreign-currency invoice must also state each bucket's VAT in PLN
  (P_14_xW), which needs the exchange rate the taxpayer applied (the NBP
  rate from the prior business day) -- asked for, not looked up.
- A correction (KOR) carries negative differences and references the
  corrected invoice, with its KSeF number when it had one.
- The seller NIP is checksum-validated (KSeF rejects a bad NIP outright).

Transmission: KSeF 2.0 requires an authenticated session (token or XAdES
challenge) and AES-encrypted invoice upload; that protocol runs through an
integrator/gateway configured by KSEF_BASE_URL / KSEF_API_KEY. With none
configured the FA(3) document is still generated and stored.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from lxml import etree as ET

from .base import (
    DocInput,
    EInvoiceDataMissing,
    FieldSpec,
    NationalFormat,
    fmt,
    resolve_line_value,
)
from .transport import IntermediaryClient

NS = "http://crd.gov.pl/wzor/2025/06/25/13775/"

EU = {"AT", "BE", "BG", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "GR", "HR", "HU", "IE", "IT",
      "LV", "LT", "LU", "MT", "NL", "PT", "RO", "SK", "SI", "ES", "SE", "XI"}

ZERO_CODES = (
    ("0 KR", "0% krajowe (domestic 0%)"),
    ("0 WDT", "0% WDT (intra-EU supply)"),
    ("0 EX", "0% eksport (export)"),
    ("zw", "zw - zwolnione (exempt)"),
    ("np I", "np I - poza terytorium kraju (outside PL)"),
    ("np II", "np II - art. 100 ust. 1 pkt 4 (EU services, art. 28b)"),
    ("oo", "oo - odwrotne obciążenie (reverse charge)"),
)
FORMA_PLATNOSCI = (
    ("1", "1 gotówka"), ("2", "2 karta"), ("3", "3 bon"), ("4", "4 czek"),
    ("5", "5 kredyt"), ("6", "6 przelew"), ("7", "7 mobilna"),
)
YES_NO = (("1", "1 tak (yes)"), ("2", "2 nie (no)"))

# standard-rate bucket per percentage (P_13_1..4). 23/22 share a bucket, as
# do 8/7 -- the reduced rates moved over time and the form keeps both.
_BUCKET = {Decimal("23"): 1, Decimal("22"): 1, Decimal("8"): 2, Decimal("7"): 2,
           Decimal("5"): 3, Decimal("4"): 4, Decimal("3"): 4}
_ZERO_FIELD = {"0 KR": "P_13_6_1", "0 WDT": "P_13_6_2", "0 EX": "P_13_6_3", "zw": "P_13_7",
               "np I": "P_13_8", "np II": "P_13_9", "oo": "P_13_10"}

_zero_rated = lambda doc, line: Decimal(line.tax_percent) == 0  # noqa: E731


def _has_exempt(doc, _party=None) -> bool:
    spec = next(f for f in PlKsef.fields if f.key == "stawka_zero")
    return any(_zero_rated(doc, l) and resolve_line_value(spec, doc, l) == "zw" for l in doc.lines)


def nip_valid(nip: str) -> bool:
    digits = re.sub(r"\D", "", nip or "")
    if len(digits) != 10:
        return False
    weights = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    check = sum(int(d) * w for d, w in zip(digits, weights)) % 11
    return check != 10 and check == int(digits[9])


class PlKsef(NationalFormat):
    mode = "pl_ksef"
    label = "Poland - KSeF FA(3)"
    countries = ("PL",)
    xsd = "pl/schemat_FA3.xsd"
    fields = [
        FieldSpec("seller", "tax_id", "NIP", pattern=r"\d{10}"),
        FieldSpec("seller", "name", "Nazwa"),
        FieldSpec("seller", "street", "Ulica i numer (AdresL1)"),
        FieldSpec("seller", "postal_code", "Kod pocztowy", pattern=r"\d{2}-\d{3}"),
        FieldSpec("seller", "city", "Miejscowość"),
        FieldSpec("seller", "metoda_kasowa", "Metoda kasowa (P_16)", choices=YES_NO,
                  help="Cash-accounting method election. '2' unless the taxpayer opted in."),
        FieldSpec("seller", "default_stawka_zero", "Default basis for 0% lines", required=False,
                  choices=ZERO_CODES),
        FieldSpec("seller", "zwolnienie_podstawa", "Podstawa zwolnienia (P_19A)", when=_has_exempt,
                  help="Legal basis of the VAT exemption, e.g. 'art. 43 ust. 1 pkt 37 ustawy o VAT'."),
        FieldSpec("seller", "forma_platnosci", "Forma płatności", required=False, choices=FORMA_PLATNOSCI),
        FieldSpec("seller", "iban", "Rachunek bankowy (NRB/IBAN)", required=False, pattern=r"[A-Z0-9]{10,34}"),
        FieldSpec("buyer", "name", "Nazwa nabywcy"),
        FieldSpec("buyer", "country_code", "Kraj nabywcy", pattern=r"[A-Z]{2}"),
        FieldSpec("buyer", "jst", "JST (jednostka samorządu terytorialnego)", required=False, choices=YES_NO,
                  help="'1' only if the buyer is a subordinate local-government unit. Defaults to 2."),
        FieldSpec("buyer", "gv", "GV (członek grupy VAT)", required=False, choices=YES_NO,
                  help="'1' only if the buyer is a VAT group member. Defaults to 2."),
        FieldSpec("line", "stawka_zero", "Stawka 0% / zw / np / oo", choices=ZERO_CODES, when=_zero_rated,
                  default_from="default_stawka_zero"),
        FieldSpec("line", "unit", "Jednostka miary (P_8A)", required=False),
        FieldSpec("document", "kurs_waluty", "Kurs waluty (NBP)", pattern=r"\d{1,6}(\.\d{1,6})?",
                  when=lambda doc, _o: (doc.currency or "").upper() != "PLN",
                  help="PLN per 1 unit of the invoice currency (NBP mid rate, prior business day)."),
    ]

    def validate(self, doc: DocInput) -> None:
        problems: list[dict] = []
        try:
            super().validate(doc)
        except EInvoiceDataMissing as exc:
            problems = exc.problems
        if doc.seller.tax_id and re.fullmatch(r"\d{10}", doc.seller.tax_id) and not nip_valid(doc.seller.tax_id):
            problems.append({"scope": "seller", "key": "tax_id", "label": "NIP", "message": "NIP checksum is invalid"})
        buyer_country = (doc.buyer.country_code or "").upper()
        if buyer_country == "PL" and doc.buyer.tax_id and not nip_valid(doc.buyer.tax_id):
            problems.append({"scope": "buyer", "key": "tax_id", "label": "NIP nabywcy",
                             "message": "NIP checksum is invalid"})
        for i, line in enumerate(doc.lines, start=1):
            rate = Decimal(line.tax_percent)
            if rate != 0 and rate not in _BUCKET:
                problems.append({"scope": f"line[{i}]", "key": "tax_percent", "label": "Stawka",
                                 "message": f"{rate}% is not a Polish VAT rate (23/8/5/4/0)"})
        if doc.is_credit_note and not doc.original_number:
            problems.append({"scope": "document", "key": "original_number", "label": "Faktura korygowana",
                             "message": "a correction (KOR) must reference the corrected invoice"})
        if problems:
            raise EInvoiceDataMissing(self.mode, problems)

    def _code(self, doc: DocInput, line) -> str:
        rate = Decimal(line.tax_percent)
        if rate == 0:
            spec = next(f for f in self.fields if f.key == "stawka_zero")
            return resolve_line_value(spec, doc, line)
        return str(rate.normalize().quantize(Decimal(1)))

    def build(self, doc: DocInput) -> str:
        self.validate(doc)
        sign = Decimal("-1") if doc.is_credit_note else Decimal("1")
        pln = (doc.currency or "").upper() == "PLN"
        rate_pln = None if pln else Decimal(str(doc.get("kurs_waluty")))

        root = ET.Element(f"{{{NS}}}Faktura", nsmap={None: NS})
        hdr = _e(root, "Naglowek")
        kf = _e(hdr, "KodFormularza", "FA")
        kf.set("kodSystemowy", "FA (3)")
        kf.set("wersjaSchemy", "1-0E")
        _e(hdr, "WariantFormularza", "3")
        _e(hdr, "DataWytworzeniaFa", datetime.now(timezone.utc).replace(microsecond=0)
           .isoformat().replace("+00:00", "Z"))
        _e(hdr, "SystemInfo", "CyCom ERP")

        p1 = _e(root, "Podmiot1")
        di = _e(p1, "DaneIdentyfikacyjne")
        _e(di, "NIP", re.sub(r"\D", "", doc.seller.tax_id))
        _e(di, "Nazwa", _txt(doc.seller.name, 512))
        _adres(p1, "PL", doc.seller)
        if doc.seller.email:
            dk = _e(p1, "DaneKontaktowe")
            _e(dk, "Email", doc.seller.email)

        p2 = _e(root, "Podmiot2")
        di = _e(p2, "DaneIdentyfikacyjne")
        country = (doc.buyer.country_code or "").upper()
        tax_id = re.sub(r"[\s-]", "", doc.buyer.tax_id or "").upper()
        if country == "PL" and tax_id:
            _e(di, "NIP", re.sub(r"\D", "", tax_id))
        elif country in EU and tax_id:
            code = "EL" if country == "GR" else country
            _e(di, "KodUE", code)
            _e(di, "NrVatUE", tax_id[2:] if tax_id.startswith(code) else tax_id)
        elif tax_id:
            _e(di, "KodKraju", country)
            _e(di, "NrID", tax_id[:50])
        else:
            _e(di, "BrakID", "1")  # consumer / no tax id
        _e(di, "Nazwa", _txt(doc.buyer.name, 512))
        if doc.buyer.street:
            _adres(p2, country, doc.buyer)
        _e(p2, "JST", doc.buyer.get("jst") or "2")
        _e(p2, "GV", doc.buyer.get("gv") or "2")

        fa = _e(root, "Fa")
        _e(fa, "KodWaluty", doc.currency.upper())
        _e(fa, "P_1", doc.issue_dt.date().isoformat())
        if doc.seller.city:
            _e(fa, "P_1M", _txt(doc.seller.city, 256))
        _e(fa, "P_2", _txt(doc.number, 256))

        buckets: dict[int, list[Decimal]] = {}
        zero: dict[str, Decimal] = {}
        for line in doc.lines:
            code = self._code(doc, line)
            if Decimal(line.tax_percent) == 0:
                zero[code] = zero.get(code, Decimal("0")) + line.net
            else:
                b = buckets.setdefault(_BUCKET[Decimal(line.tax_percent)], [Decimal("0"), Decimal("0")])
                b[0] += line.net
                b[1] += line.tax
        gross = Decimal("0")
        for n in (1, 2, 3, 4):
            if n in buckets:
                net, tax = buckets[n]
                gross += net + tax
                _e(fa, f"P_13_{n}", fmt(sign * net, 2))
                _e(fa, f"P_14_{n}", fmt(sign * tax, 2))
                if rate_pln is not None:
                    _e(fa, f"P_14_{n}W", fmt(sign * (tax * rate_pln).quantize(Decimal("0.01"), ROUND_HALF_UP), 2))
        for code, field_name in _ZERO_FIELD.items():
            if code in zero:
                gross += zero[code]
                _e(fa, field_name, fmt(sign * zero[code], 2))
        _e(fa, "P_15", fmt(sign * gross, 2))

        adn = _e(fa, "Adnotacje")
        _e(adn, "P_16", doc.seller.get("metoda_kasowa"))
        _e(adn, "P_17", "2")                                   # not self-billed
        _e(adn, "P_18", "1" if "oo" in zero else "2")          # reverse charge
        _e(adn, "P_18A", "2")                                  # MPP split payment
        zw = _e(adn, "Zwolnienie")
        if "zw" in zero:
            _e(zw, "P_19", "1")
            _e(zw, "P_19A", _txt(doc.seller.get("zwolnienie_podstawa"), 256))
        else:
            _e(zw, "P_19N", "1")
        nst = _e(adn, "NoweSrodkiTransportu")
        _e(nst, "P_22N", "1")
        _e(adn, "P_23", "2")                                   # not a triangular simplified supply
        pm = _e(adn, "PMarzy")
        _e(pm, "P_PMarzyN", "1")

        _e(fa, "RodzajFaktury", "KOR" if doc.is_credit_note else "VAT")
        if doc.is_credit_note:
            dfk = _e(fa, "DaneFaKorygowanej")
            _e(dfk, "DataWystFaKorygowanej", (doc.original_date or doc.issue_dt.date()).isoformat())
            _e(dfk, "NrFaKorygowanej", _txt(doc.original_number, 256))
            ksef_no = (doc.get("original_reference") or "").strip()
            if ksef_no and re.fullmatch(r"[0-9A-Z]{10}-\d{8}-[0-9A-F]{6}-?[0-9A-F]{6}-[0-9A-F]{2}", ksef_no):
                _e(dfk, "NrKSeF", "1")
                _e(dfk, "NrKSeFFaKorygowanej", ksef_no)
            else:
                _e(dfk, "NrKSeFN", "1")  # corrected invoice was issued outside KSeF

        for i, line in enumerate(doc.lines, start=1):
            w = _e(fa, "FaWiersz")
            _e(w, "NrWierszaFa", str(i))
            _e(w, "P_7", _txt(line.name, 512) or "-")
            _e(w, "P_8A", _txt(line.get("unit") or "szt.", 256))
            _e(w, "P_8B", _qty(sign * Decimal(line.quantity)))
            _e(w, "P_9A", _price(line.unit_price))
            _e(w, "P_11", fmt(sign * line.net, 2))
            _e(w, "P_12", self._code(doc, line))

        forma = doc.seller.get("forma_platnosci")
        iban = doc.seller.get("iban")
        if not doc.is_credit_note and (doc.due_date or forma or iban):
            pl = _e(fa, "Platnosc")
            if doc.due_date:
                tp = _e(pl, "TerminPlatnosci")
                _e(tp, "Termin", doc.due_date.isoformat())
            if forma:
                _e(pl, "FormaPlatnosci", forma)
            if iban:
                rb = _e(pl, "RachunekBankowy")
                _e(rb, "NrRB", re.sub(r"\s", "", iban))

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")

    def filename(self, doc: DocInput) -> str:
        return f"FA3_{re.sub(r'[^A-Za-z0-9_-]', '_', doc.number)}.xml"

    def client(self):
        return IntermediaryClient("KSEF", channel_label="KSeF integrator / gateway")


def _e(parent, tag, text=None):
    el = ET.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = str(text)
    return el


def _txt(value, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _adres(parent, country: str, party) -> None:
    a = _e(parent, "Adres")
    _e(a, "KodKraju", country or "PL")
    line1 = " ".join(x for x in (party.street, party.building_number) if x)
    _e(a, "AdresL1", _txt(line1, 512))
    line2 = " ".join(x for x in (party.postal_code, party.city) if x)
    if line2:
        _e(a, "AdresL2", _txt(line2, 512))


def _qty(q: Decimal) -> str:
    d = q.normalize()
    places = min(6, max(0, -d.as_tuple().exponent))
    return fmt(d, places) if places else str(int(d))


def _price(p) -> str:
    d = Decimal(str(p)).normalize()
    places = min(8, max(0, -d.as_tuple().exponent))
    return fmt(d, places) if places else str(int(d))
