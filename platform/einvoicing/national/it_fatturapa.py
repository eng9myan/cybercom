"""
Italy -- FatturaPA v1.2.2 (FPR12 private / FPA12 public administration),
transmitted through the Sistema di Interscambio (SdI).

Built against the Agenzia delle Entrate XSD vendored under
schemas/it/ (every builder test schema-validates its output). What the XSD
can't express but SdI rejects on, handled here explicitly:

- a zero-rated line/summary must carry a Natura (exemption nature) code;
- each DatiRiepilogo's Imposta must equal Imponibile x Aliquota (the check
  runs per summary, so tax is computed per rate group, not summed per line);
- a foreign address uses CAP "00000" and a foreign buyer is addressed with
  CodiceDestinatario "XXXXXXX" -- both documented SdI conventions, not
  guesses; everything else (tax regime, Natura, the buyer's SdI code) must
  come from the taxpayer.

Signature: optional for B2B through SdI, mandatory for invoices to the
public administration (FPA12). With FATTURAPA_PRIVATE_KEY_PATH /
FATTURAPA_CERT_PATH set, the document gets an enveloped XAdES signature;
an FPA12 invoice without a key refuses rather than sending unsigned.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from decimal import Decimal

from .base import (
    DocInput,
    FieldSpec,
    NationalFormat,
    TransportNotConfigured,
    ascii_latin,
    fmt,
    resolve_line_value,
)
from .transport import IntermediaryClient

NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"
ET.register_namespace("p", NS)

REGIME_FISCALE = (
    ("RF01", "RF01 Ordinario"), ("RF02", "RF02 Contribuenti minimi"),
    ("RF04", "RF04 Agricoltura e pesca"), ("RF05", "RF05 Vendita sali e tabacchi"),
    ("RF06", "RF06 Commercio fiammiferi"), ("RF07", "RF07 Editoria"),
    ("RF08", "RF08 Telefonia pubblica"), ("RF09", "RF09 Documenti di trasporto pubblico"),
    ("RF10", "RF10 Intrattenimenti e giochi"), ("RF11", "RF11 Agenzie viaggi e turismo"),
    ("RF12", "RF12 Agriturismo"), ("RF13", "RF13 Vendite a domicilio"),
    ("RF14", "RF14 Beni usati / oggetti d'arte"), ("RF15", "RF15 Agenzie di vendite all'asta"),
    ("RF16", "RF16 IVA per cassa P.A."), ("RF17", "RF17 IVA per cassa"),
    ("RF18", "RF18 Altro"), ("RF19", "RF19 Regime forfettario"),
)
NATURA = tuple((c, c) for c in (
    "N1", "N2.1", "N2.2", "N3.1", "N3.2", "N3.3", "N3.4", "N3.5", "N3.6", "N4", "N5",
    "N6.1", "N6.2", "N6.3", "N6.4", "N6.5", "N6.6", "N6.7", "N6.8", "N6.9", "N7",
))
MODALITA_PAGAMENTO = (
    ("MP01", "MP01 Contanti"), ("MP02", "MP02 Assegno"), ("MP05", "MP05 Bonifico"),
    ("MP08", "MP08 Carta di pagamento"), ("MP12", "MP12 RIBA"), ("MP19", "MP19 SEPA Direct Debit"),
)

_is_it = lambda doc, party: (party.country_code or "").upper() == "IT"  # noqa: E731
_zero_rated = lambda doc, line: Decimal(line.tax_percent) == 0  # noqa: E731


class ItFatturaPA(NationalFormat):
    mode = "it_fatturapa"
    label = "Italy - FatturaPA via SdI"
    countries = ("IT",)
    xsd = "it/Schema_del_file_xml_FatturaPA_v1.2.2.xsd"
    fields = [
        FieldSpec("seller", "tax_id", "Partita IVA", pattern=r"\d{11}"),
        FieldSpec("seller", "name", "Denominazione"),
        FieldSpec("seller", "regime_fiscale", "Regime fiscale", choices=REGIME_FISCALE),
        FieldSpec("seller", "street", "Indirizzo (sede)"),
        FieldSpec("seller", "building_number", "Numero civico", required=False, pattern=r"[^\s]{1,8}"),
        FieldSpec("seller", "postal_code", "CAP", pattern=r"\d{5}"),
        FieldSpec("seller", "city", "Comune"),
        FieldSpec("seller", "region", "Provincia (sigla)", required=False, pattern=r"[A-Z]{2}"),
        FieldSpec("seller", "codice_fiscale", "Codice fiscale", required=False, pattern=r"[A-Z0-9]{11,16}"),
        FieldSpec("seller", "default_natura", "Default Natura for zero-rated lines", required=False,
                  choices=NATURA, help="Used for a 0% line that has no Natura of its own."),
        FieldSpec("seller", "modalita_pagamento", "Modalita di pagamento", required=False,
                  choices=MODALITA_PAGAMENTO, help="Adds a DatiPagamento block when the invoice has a due date."),
        FieldSpec("seller", "iban", "IBAN", required=False, pattern=r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}"),
        FieldSpec("buyer", "name", "Denominazione"),
        FieldSpec("buyer", "street", "Indirizzo"),
        FieldSpec("buyer", "city", "Comune / city"),
        FieldSpec("buyer", "country_code", "Nazione", pattern=r"[A-Z]{2}"),
        FieldSpec("buyer", "postal_code", "CAP", pattern=r"\d{5}", when=_is_it),
        FieldSpec("buyer", "codice_destinatario", "Codice destinatario SdI", pattern=r"[A-Z0-9]{6,7}",
                  when=_is_it, help="7 characters (B2B), 6 for a public administration office; "
                                    "'0000000' when delivering via PEC or to a consumer."),
        FieldSpec("buyer", "pec", "PEC destinatario", required=False, pattern=r"[^@\s]+@[^@\s]+\.[^@\s]+"),
        FieldSpec("buyer", "codice_fiscale", "Codice fiscale", required=False, pattern=r"[A-Z0-9]{11,16}"),
        FieldSpec("line", "natura", "Natura (0% VAT)", choices=NATURA, when=_zero_rated,
                  default_from="default_natura"),
    ]

    def validate(self, doc: DocInput) -> None:
        super().validate(doc)
        from .base import EInvoiceDataMissing

        problems = []
        if not re.search(r"\d", doc.number or ""):
            problems.append({"scope": "document", "key": "number", "label": "Numero",
                             "message": "SdI requires the invoice number to contain a digit"})
        buyer_it = _is_it(doc, doc.buyer)
        if buyer_it and not (doc.buyer.tax_id or doc.buyer.get("codice_fiscale")):
            problems.append({"scope": "buyer", "key": "tax_id", "label": "Partita IVA / Codice fiscale",
                             "message": "an Italian buyer needs a Partita IVA or a Codice fiscale"})
        if not buyer_it and not doc.buyer.tax_id:
            problems.append({"scope": "buyer", "key": "tax_id", "label": "VAT / tax id",
                             "message": "a foreign buyer needs a tax identifier"})
        if doc.is_credit_note and not doc.original_number:
            problems.append({"scope": "document", "key": "original_number", "label": "Fattura collegata",
                             "message": "a credit note (TD04) must reference the invoice it corrects"})
        if problems:
            raise EInvoiceDataMissing(self.mode, problems)

    # -- helpers --------------------------------------------------------------
    @staticmethod
    def progressivo(icv: int) -> str:
        """5-char base36 counter, the conventional SdI file progressive."""
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        n, out = max(int(icv), 0), ""
        while True:
            n, r = divmod(n, 36)
            out = digits[r] + out
            if n == 0:
                break
        return out.rjust(5, "0")[-5:]

    def filename(self, doc: DocInput) -> str:
        return f"IT{doc.seller.tax_id}_{self.progressivo(doc.icv)}.xml"

    def _natura(self, doc: DocInput, line) -> str | None:
        if Decimal(line.tax_percent) != 0:
            return None
        spec = next(f for f in self.fields if f.key == "natura")
        return resolve_line_value(spec, doc, line)

    # -- build ------------------------------------------------------------------
    def build(self, doc: DocInput) -> str:
        self.validate(doc)
        buyer_it = _is_it(doc, doc.buyer)
        dest = (doc.buyer.get("codice_destinatario") or "").strip() if buyer_it else "XXXXXXX"
        formato = "FPA12" if len(dest) == 6 else "FPR12"

        root = ET.Element(f"{{{NS}}}FatturaElettronica", {"versione": formato})
        header = _e(root, "FatturaElettronicaHeader")

        dt = _e(header, "DatiTrasmissione")
        idt = _e(dt, "IdTrasmittente")
        _e(idt, "IdPaese", "IT")
        _e(idt, "IdCodice", doc.seller.get("codice_fiscale") or doc.seller.tax_id)
        _e(dt, "ProgressivoInvio", self.progressivo(doc.icv))
        _e(dt, "FormatoTrasmissione", formato)
        _e(dt, "CodiceDestinatario", dest)
        pec = (doc.buyer.get("pec") or "").strip()
        if pec and buyer_it:
            _e(dt, "PECDestinatario", pec)

        ced = _e(header, "CedentePrestatore")
        da = _e(ced, "DatiAnagrafici")
        iva = _e(da, "IdFiscaleIVA")
        _e(iva, "IdPaese", "IT")
        _e(iva, "IdCodice", doc.seller.tax_id)
        if doc.seller.get("codice_fiscale"):
            _e(da, "CodiceFiscale", doc.seller.get("codice_fiscale"))
        an = _e(da, "Anagrafica")
        _e(an, "Denominazione", ascii_latin(doc.seller.name, 80))
        _e(da, "RegimeFiscale", doc.seller.get("regime_fiscale"))
        _sede(ced, doc.seller, "IT")

        ces = _e(header, "CessionarioCommittente")
        da = _e(ces, "DatiAnagrafici")
        if doc.buyer.tax_id:
            iva = _e(da, "IdFiscaleIVA")
            country = (doc.buyer.country_code or "IT").upper()
            _e(iva, "IdPaese", country)
            _e(iva, "IdCodice", _strip_country(doc.buyer.tax_id, country)[:28])
        if doc.buyer.get("codice_fiscale"):
            _e(da, "CodiceFiscale", doc.buyer.get("codice_fiscale"))
        an = _e(da, "Anagrafica")
        _e(an, "Denominazione", ascii_latin(doc.buyer.name, 80))
        _sede(ces, doc.buyer, (doc.buyer.country_code or "IT").upper())

        body = _e(root, "FatturaElettronicaBody")
        dg = _e(body, "DatiGenerali")
        dgd = _e(dg, "DatiGeneraliDocumento")
        _e(dgd, "TipoDocumento", "TD04" if doc.is_credit_note else "TD01")
        _e(dgd, "Divisa", doc.currency.upper())
        _e(dgd, "Data", doc.issue_dt.date().isoformat())
        _e(dgd, "Numero", doc.number[:20])

        # Per-summary tax (SdI checks Imposta == Imponibile x Aliquota per
        # DatiRiepilogo), keyed by (rate, natura).
        groups: dict[tuple[Decimal, str | None], Decimal] = {}
        for line in doc.lines:
            key = (Decimal(line.tax_percent), self._natura(doc, line))
            groups[key] = groups.get(key, Decimal("0")) + line.net
        summaries = [
            (rate, natura, taxable, (taxable * rate / 100).quantize(Decimal("0.01")))
            for (rate, natura), taxable in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] or ""))
        ]
        total = sum((t + tax for _r, _n, t, tax in summaries), Decimal("0"))
        _e(dgd, "ImportoTotaleDocumento", fmt(total, 2))

        if doc.is_credit_note:
            fc = _e(dg, "DatiFattureCollegate")
            _e(fc, "IdDocumento", doc.original_number[:20])
            if doc.original_date:
                _e(fc, "Data", doc.original_date.isoformat())

        dbs = _e(body, "DatiBeniServizi")
        for i, line in enumerate(doc.lines, start=1):
            dl = _e(dbs, "DettaglioLinee")
            _e(dl, "NumeroLinea", str(i))
            _e(dl, "Descrizione", ascii_latin(line.name, 1000) or "-")
            _e(dl, "Quantita", _decimals(line.quantity, 2, 8))
            _e(dl, "PrezzoUnitario", _decimals(line.unit_price, 2, 8))
            _e(dl, "PrezzoTotale", fmt(line.net, 2))
            _e(dl, "AliquotaIVA", fmt(line.tax_percent, 2))
            natura = self._natura(doc, line)
            if natura:
                _e(dl, "Natura", natura)
        for rate, natura, taxable, tax in summaries:
            dr = _e(dbs, "DatiRiepilogo")
            _e(dr, "AliquotaIVA", fmt(rate, 2))
            if natura:
                _e(dr, "Natura", natura)
            _e(dr, "ImponibileImporto", fmt(taxable, 2))
            _e(dr, "Imposta", fmt(tax, 2))
            if not natura:
                _e(dr, "EsigibilitaIVA", "I")

        modalita = doc.seller.get("modalita_pagamento")
        if modalita and doc.due_date and not doc.is_credit_note:
            dp = _e(body, "DatiPagamento")
            _e(dp, "CondizioniPagamento", "TP02")
            det = _e(dp, "DettaglioPagamento")
            _e(det, "ModalitaPagamento", modalita)
            _e(det, "DataScadenzaPagamento", doc.due_date.isoformat())
            _e(det, "ImportoPagamento", fmt(total, 2))
            if doc.seller.get("iban"):
                _e(det, "IBAN", doc.seller.get("iban"))

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")

    def signing_status(self) -> bool:
        from ..signing import KEY_LOADER

        key_pem, cert_pem = KEY_LOADER(self.mode)
        return bool(key_pem and cert_pem)

    def signing_problems(self, doc: DocInput) -> list[dict]:
        from ..signing import KEY_LOADER

        dest = (doc.buyer.get("codice_destinatario") or "").strip()
        if _is_it(doc, doc.buyer) and len(dest) == 6:
            key_pem, cert_pem = KEY_LOADER(self.mode)
            if not (key_pem and cert_pem):
                return [{"scope": "seller", "key": "certificate", "label": "Firma digitale (FPA12)",
                         "message": "invoices to the public administration must be signed -- install the "
                                    "qualified certificate (FATTURAPA_PRIVATE_KEY_PATH / FATTURAPA_CERT_PATH)"}]
        return []

    def sign(self, document: str, doc: DocInput) -> str:
        from ..signing import KEY_LOADER, XAdESSigner

        key_pem, cert_pem = KEY_LOADER(self.mode)
        if key_pem and cert_pem:
            return XAdESSigner(key_pem, cert_pem).sign(document)
        if 'versione="FPA12"' in document:
            raise TransportNotConfigured(
                "Invoices to the Italian public administration (FPA12) must be signed. Set "
                "FATTURAPA_PRIVATE_KEY_PATH and FATTURAPA_CERT_PATH to the qualified certificate."
            )
        return document  # B2B via SdI: signature optional

    def client(self):
        return IntermediaryClient("SDI", channel_label="SdI channel / intermediary")


def _e(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = str(text)
    return el


def _sede(parent: ET.Element, party, country: str) -> None:
    sede = _e(parent, "Sede")
    _e(sede, "Indirizzo", ascii_latin(party.street, 60))
    if party.building_number:
        _e(sede, "NumeroCivico", party.building_number[:8])
    # SdI convention: a non-Italian address carries CAP 00000
    _e(sede, "CAP", party.postal_code if country == "IT" else "00000")
    _e(sede, "Comune", ascii_latin(party.city, 60))
    if country == "IT" and party.region:
        _e(sede, "Provincia", party.region.upper())
    _e(sede, "Nazione", country)


def _strip_country(tax_id: str, country: str) -> str:
    tid = re.sub(r"\s", "", tax_id or "").upper()
    return tid[2:] if tid.startswith(country) and len(tid) > 2 else tid


def _decimals(value, min_places: int, max_places: int) -> str:
    """Render with as many decimals as the value needs, within the XSD's
    [min, max] window (Quantita/PrezzoUnitario allow 2-8)."""
    d = Decimal(str(value)).normalize()
    places = max(min_places, min(max_places, -d.as_tuple().exponent if d.as_tuple().exponent < 0 else 0))
    return fmt(d, places)
