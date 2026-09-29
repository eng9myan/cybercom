"""
Spain -- SII (Suministro Inmediato de Información), libro registro de
facturas expedidas, schema version 1.1, built against the AEAT XSDs
vendored under schemas/es/.

SII is a *reporting* obligation (each issued invoice is reported to the AEAT
within four days), not a document sent to the customer, and it only
applies to taxpayers registered in it (large companies, VAT groups,
REDEME, voluntary registrants). A tenant whose issuer profile says it is not
an SII filer gets `not_applicable` -- VERI*FACTU and TicketBAI, the regimes
for everyone else, are separate systems this module does not claim.

Handled explicitly:
- NIF/NIE/CIF check characters are validated (the AEAT rejects bad ones).
- VAT is broken down per rate (DetalleIVA); 0% lines must say *why*:
  exempt (with its CausaExencion E1-E6), not subject (art. 7/14 or by
  place-of-supply rules), or reverse charge (inversión del sujeto pasivo);
  never guessed.
- A foreign counterparty is identified with IDOtro (02 = EU VAT number,
  04 passport / official id, 06 other) and its invoice is broken down by
  operation type (Entrega vs PrestacionServicios), as the AEAT requires.
- A rectificativa (credit note) is R1-R4 "por diferencias" with negative
  amounts, and references the invoice it corrects.
- Transmission is SOAP with a client certificate to the AEAT, run by a
  gateway configured as SII_BASE_URL / SII_API_KEY.
"""
from __future__ import annotations

import re
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

_BASE = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/ssii/fact/ws/"
LR = _BASE + "SuministroLR.xsd"
SII = _BASE + "SuministroInformacion.xsd"
EU = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "GR", "FI", "FR", "HR", "HU", "IE", "IT", "LT",
      "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"}
_RATES = {Decimal(x) for x in ("21", "10", "5", "4", "2", "7.5")}

CLAVE_REGIMEN = (
    ("01", "01 Régimen general"), ("02", "02 Exportación"), ("03", "03 Bienes usados / arte (REBU)"),
    ("05", "05 Agencias de viajes"), ("07", "07 Criterio de caja"), ("08", "08 IPSI / IGIC"),
    ("09", "09 Mediación agencias de viajes"), ("11", "11 Arrendamiento local de negocio"),
    ("14", "14 Obra pública (AAPP)"), ("15", "15 Tracto sucesivo"),
)
TRATAMIENTO_CERO = (
    ("exenta", "Exenta"), ("no_sujeta_art7_14", "No sujeta (art. 7, 14 u otros)"),
    ("no_sujeta_localizacion", "No sujeta por reglas de localización"),
    ("isp", "Inversión del sujeto pasivo"),
)
CAUSA_EXENCION = tuple((c, c) for c in ("E1", "E2", "E3", "E4", "E5", "E6"))
TIPO_R = (("R1", "R1 Art. 80.1, 80.2 y 80.6 LIVA"), ("R2", "R2 Art. 80.3 LIVA (concurso)"),
          ("R3", "R3 Art. 80.4 LIVA (incobrables)"), ("R4", "R4 Resto"))

_zero = lambda doc, line: Decimal(line.tax_percent) == 0  # noqa: E731
_foreign = lambda doc, p: bool(p.country_code) and (p.country_code or "").upper() != "ES"  # noqa: E731


def _treatment(doc, line):
    return resolve_line_value(next(f for f in EsSii.fields if f.key == "tratamiento_cero"), doc, line)


def nif_valid(nif: str) -> bool:
    n = (nif or "").strip().upper()
    letters = "TRWAGMYFPDXBNJZSQVHLCKE"
    if re.fullmatch(r"\d{8}[A-Z]", n):                       # DNI
        return letters[int(n[:8]) % 23] == n[8]
    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", n):                   # NIE
        return letters[int(str("XYZ".index(n[0])) + n[1:8]) % 23] == n[8]
    if re.fullmatch(r"[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]", n):  # CIF
        digits = n[1:8]
        even = sum(int(d) for d in digits[1::2])
        odd = sum(sum(divmod(int(d) * 2, 10)) for d in digits[0::2])
        control = (10 - (even + odd) % 10) % 10
        return n[8] in (str(control), "JABCDEFGHI"[control])
    return False


class EsSii(NationalFormat):
    mode = "es_sii"
    label = "Spain - SII (libro de facturas expedidas)"
    countries = ("ES",)
    xsd = "es/SuministroLR.xsd"
    fields = [
        FieldSpec("seller", "sii_obligado", "Registered in SII", choices=(("S", "Yes"), ("N", "No")),
                  help="Only SII filers report here; others use VERI*FACTU / TicketBAI (not covered)."),
        FieldSpec("seller", "tax_id", "NIF", pattern=r"[0-9A-Z]{9}"),
        FieldSpec("seller", "name", "Nombre o razón social"),
        FieldSpec("seller", "clave_regimen", "Clave de régimen (default)", choices=CLAVE_REGIMEN),
        FieldSpec("seller", "descripcion_operacion", "Descripción de la operación (default)",
                  help="e.g. 'Venta de mercaderías' or 'Prestación de servicios'."),
        FieldSpec("seller", "default_tratamiento_cero", "0% line treatment (default)", required=False,
                  choices=TRATAMIENTO_CERO),
        FieldSpec("seller", "default_causa_exencion", "Causa de exención (default)", required=False,
                  choices=CAUSA_EXENCION),
        FieldSpec("seller", "default_tipo_operacion", "Operation type for foreign buyers (default)", required=False,
                  choices=(("entrega", "Entrega de bienes"), ("servicio", "Prestación de servicios"))),
        FieldSpec("buyer", "name", "Nombre o razón social"),
        FieldSpec("buyer", "country_code", "País", pattern=r"[A-Z]{2}"),
        FieldSpec("buyer", "tax_id", "NIF / VAT / ID", required=False),
        FieldSpec("buyer", "id_type", "Tipo de identificación (IDOtro)", required=False,
                  choices=(("02", "02 NIF-IVA (EU VAT)"), ("03", "03 Pasaporte"), ("04", "04 Documento oficial"),
                           ("05", "05 Certificado de residencia"), ("06", "06 Otro documento")),
                  when=_foreign, help="Defaults to 02 for an EU VAT number, 06 otherwise."),
        FieldSpec("line", "tratamiento_cero", "Tratamiento 0%", choices=TRATAMIENTO_CERO, when=_zero,
                  default_from="default_tratamiento_cero"),
        FieldSpec("line", "causa_exencion", "Causa de exención", choices=CAUSA_EXENCION,
                  when=lambda doc, line: _zero(doc, line) and _treatment(doc, line) == "exenta",
                  default_from="default_causa_exencion"),
        FieldSpec("line", "tipo_operacion", "Entrega / servicio",
                  choices=(("entrega", "Entrega"), ("servicio", "Servicio")),
                  when=lambda doc, line: _foreign(doc, doc.buyer), default_from="default_tipo_operacion"),
        FieldSpec("document", "tipo_rectificativa", "Tipo de rectificativa", choices=TIPO_R,
                  when=lambda doc, _o: doc.is_credit_note),
        FieldSpec("document", "clave_regimen", "Clave de régimen (this invoice)", required=False,
                  choices=CLAVE_REGIMEN),
    ]

    def not_applicable_reason(self, doc: DocInput) -> str | None:
        if doc.seller.get("sii_obligado") == "N":
            return ("This taxpayer is not registered in the SII; its invoices are reported through "
                    "VERI*FACTU or TicketBAI, which are not covered by this module.")
        return None

    def validate(self, doc: DocInput) -> None:
        problems: list[dict] = []
        try:
            super().validate(doc)
        except EInvoiceDataMissing as exc:
            problems = exc.problems
        if doc.seller.tax_id and not nif_valid(doc.seller.tax_id):
            problems.append({"scope": "seller", "key": "tax_id", "label": "NIF", "message": "NIF check character is invalid"})
        foreign = _foreign(doc, doc.buyer)
        if not foreign and not doc.buyer.tax_id:
            problems.append({"scope": "buyer", "key": "tax_id", "label": "NIF",
                             "message": "a Spanish counterparty needs its NIF (F1 invoice)"})
        elif not foreign and not nif_valid(doc.buyer.tax_id):
            problems.append({"scope": "buyer", "key": "tax_id", "label": "NIF", "message": "NIF check character is invalid"})
        if foreign and not doc.buyer.tax_id:
            problems.append({"scope": "buyer", "key": "tax_id", "label": "ID",
                             "message": "a foreign counterparty needs a VAT number or other identifier"})
        for i, line in enumerate(doc.lines, start=1):
            rate = Decimal(line.tax_percent).normalize()
            if rate != 0 and rate not in _RATES:
                problems.append({"scope": f"line[{i}]", "key": "tax_percent", "label": "Tipo IVA",
                                 "message": f"{line.tax_percent}% is not a Spanish VAT rate"})
        if doc.is_credit_note and not doc.original_number:
            problems.append({"scope": "document", "key": "original_number", "label": "Factura rectificada",
                             "message": "a rectificativa must reference the invoice it corrects"})
        if problems:
            raise EInvoiceDataMissing(self.mode, problems)

    def build(self, doc: DocInput) -> str:
        self.validate(doc)
        sign = Decimal("-1") if doc.is_credit_note else Decimal("1")
        foreign = _foreign(doc, doc.buyer)

        root = ET.Element(f"{{{LR}}}SuministroLRFacturasEmitidas", nsmap={"siiLR": LR, "sii": SII})
        cab = _s(root, "Cabecera")
        _s(cab, "IDVersionSii", "1.1")
        tit = _s(cab, "Titular")
        _s(tit, "NombreRazon", _txt(doc.seller.name, 120))
        _s(tit, "NIF", doc.seller.tax_id.upper())
        _s(cab, "TipoComunicacion", "A0")

        reg = _lr(root, "RegistroLRFacturasEmitidas")
        per = _s(reg, "PeriodoLiquidacion")
        _s(per, "Ejercicio", str(doc.issue_dt.year))
        _s(per, "Periodo", f"{doc.issue_dt.month:02d}")
        idf = _lr(reg, "IDFactura")
        _s(_s(idf, "IDEmisorFactura"), "NIF", doc.seller.tax_id.upper())
        _s(idf, "NumSerieFacturaEmisor", _txt(doc.number, 60))
        _s(idf, "FechaExpedicionFacturaEmisor", doc.issue_dt.strftime("%d-%m-%Y"))

        fe = _lr(reg, "FacturaExpedida")
        if doc.is_credit_note:
            _s(fe, "TipoFactura", doc.get("tipo_rectificativa"))
            _s(fe, "TipoRectificativa", "I")
            rect = _s(_s(fe, "FacturasRectificadas"), "IDFacturaRectificada")
            _s(rect, "NumSerieFacturaEmisor", _txt(doc.original_number, 60))
            _s(rect, "FechaExpedicionFacturaEmisor", (doc.original_date or doc.issue_dt.date()).strftime("%d-%m-%Y"))
        else:
            _s(fe, "TipoFactura", "F1")
        _s(fe, "ClaveRegimenEspecialOTrascendencia", doc.get("clave_regimen") or doc.seller.get("clave_regimen"))
        _s(fe, "ImporteTotal", fmt(sign * doc.gross_total, 2))
        _s(fe, "DescripcionOperacion", _txt(doc.get("descripcion_operacion") or doc.seller.get("descripcion_operacion"), 500))

        cp = _s(fe, "Contraparte")
        _s(cp, "NombreRazon", _txt(doc.buyer.name, 120))
        if foreign:
            country = doc.buyer.country_code.upper()
            tid = re.sub(r"\s", "", doc.buyer.tax_id).upper()
            id_type = doc.buyer.get("id_type") or ("02" if country in EU else "06")
            other = _s(cp, "IDOtro")
            _s(other, "CodigoPais", country)
            _s(other, "IDType", id_type)
            _s(other, "ID", tid[:20])
        else:
            _s(cp, "NIF", doc.buyer.tax_id.upper())

        td = _s(fe, "TipoDesglose")
        if foreign:
            dto = _s(td, "DesgloseTipoOperacion")
            groups = {"servicio": [], "entrega": []}
            spec = next(f for f in self.fields if f.key == "tipo_operacion")
            for line in doc.lines:
                groups[resolve_line_value(spec, doc, line)].append(line)
            if groups["servicio"]:
                self._desglose(_s(dto, "PrestacionServicios"), doc, groups["servicio"], sign)
            if groups["entrega"]:
                self._desglose(_s(dto, "Entrega"), doc, groups["entrega"], sign)
        else:
            self._desglose(_s(td, "DesgloseFactura"), doc, doc.lines, sign)

        return ET.tostring(root, encoding="UTF-8", xml_declaration=True).decode("utf-8")

    def _desglose(self, parent, doc: DocInput, lines, sign: Decimal) -> None:
        exentas: dict[str, Decimal] = {}
        normal: dict[Decimal, Decimal] = {}
        isp = Decimal("0")
        no_sujeta = {"no_sujeta_art7_14": Decimal("0"), "no_sujeta_localizacion": Decimal("0")}
        causa_spec = next(f for f in self.fields if f.key == "causa_exencion")
        for line in lines:
            if Decimal(line.tax_percent) > 0:
                rate = Decimal(line.tax_percent).normalize()
                normal[rate] = normal.get(rate, Decimal("0")) + line.net
                continue
            t = _treatment(doc, line)
            if t == "exenta":
                causa = resolve_line_value(causa_spec, doc, line)
                exentas[causa] = exentas.get(causa, Decimal("0")) + line.net
            elif t == "isp":
                isp += line.net
            else:
                no_sujeta[t] += line.net

        if exentas or normal or isp:
            suj = _s(parent, "Sujeta")
            if exentas:
                ex = _s(suj, "Exenta")
                for causa, base in sorted(exentas.items()):
                    d = _s(ex, "DetalleExenta")
                    _s(d, "CausaExencion", causa)
                    _s(d, "BaseImponible", fmt(sign * base, 2))
            if normal or isp:
                ne = _s(suj, "NoExenta")
                _s(ne, "TipoNoExenta", "S3" if (normal and isp) else ("S2" if isp else "S1"))
                di = _s(ne, "DesgloseIVA")
                for rate, base in sorted(normal.items()):
                    d = _s(di, "DetalleIVA")
                    _s(d, "TipoImpositivo", _rate(rate))
                    _s(d, "BaseImponible", fmt(sign * base, 2))
                    _s(d, "CuotaRepercutida", fmt(sign * (base * rate / 100).quantize(Decimal("0.01"), ROUND_HALF_UP), 2))
                if isp:
                    d = _s(di, "DetalleIVA")
                    _s(d, "TipoImpositivo", "0")
                    _s(d, "BaseImponible", fmt(sign * isp, 2))
                    _s(d, "CuotaRepercutida", "0.00")
        if any(no_sujeta.values()):
            ns_el = _s(parent, "NoSujeta")
            if no_sujeta["no_sujeta_art7_14"]:
                _s(ns_el, "ImportePorArticulos7_14_Otros", fmt(sign * no_sujeta["no_sujeta_art7_14"], 2))
            if no_sujeta["no_sujeta_localizacion"]:
                _s(ns_el, "ImporteTAIReglasLocalizacion", fmt(sign * no_sujeta["no_sujeta_localizacion"], 2))

    def filename(self, doc: DocInput) -> str:
        return f"SII_{doc.seller.tax_id.upper()}_{re.sub(r'[^A-Za-z0-9_-]', '_', doc.number)}.xml"

    def client(self):
        return IntermediaryClient("SII", channel_label="SII gateway (AEAT web service)")


def _s(parent, tag, text=None):
    el = ET.SubElement(parent, f"{{{SII}}}{tag}")
    if text is not None:
        el.text = str(text)
    return el


def _lr(parent, tag):
    return ET.SubElement(parent, f"{{{LR}}}{tag}")


def _txt(value, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _rate(rate: Decimal) -> str:
    r = rate.normalize()
    return str(int(r)) if r == r.to_integral_value() else format(r, "f")
