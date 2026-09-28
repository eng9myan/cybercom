"""
Mexico -- CFDI 4.0 (Anexo 20), sealed with the issuer's CSD and stamped
(timbrado) by an authorised PAC.

Built against SAT's own artefacts, vendored under schemas/mx/ and used
offline:
- cfdv40.xsd + catCFDI.xsd (the full SAT catalogues: c_ClaveProdServ,
  c_ClaveUnidad, c_CodigoPostal, c_RegimenFiscal, c_UsoCFDI, ...), so a
  product key, unit or postal code that isn't in SAT's catalogue fails
  schema validation here, before a PAC ever sees it;
- cadenaoriginal_4_0.xslt (+ its 33 includes): the cadena original is
  produced by SAT's own transform, not re-implemented, so the sello is over
  exactly the string SAT/PAC recompute.

The schema itself requires Sello/NoCertificado/Certificado, so a CFDI can't
exist unsealed: without a CSD configured (CFDI_CSD_PRIVATE_KEY_PATH,
CFDI_CSD_CERT_PATH, optional CFDI_CSD_KEY_PASSWORD -- SAT's .key/.cer in
DER or PEM) the document is reported `incomplete` with that as the missing
item, and no sequence number is used.

Stamping (timbrado) by a PAC goes through CFDI_PAC_BASE_URL/CFDI_PAC_API_KEY;
the PAC's UUID (folio fiscal) is recorded as the authority reference.
"""
from __future__ import annotations

import base64
import re
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

from lxml import etree as ET

from .base import (
    SCHEMAS_DIR,
    DocInput,
    EInvoiceDataMissing,
    FieldSpec,
    NationalFormat,
    TransportNotConfigured,
    fmt,
    resolve_line_value,
)
from .transport import IntermediaryClient

NS = "http://www.sat.gob.mx/cfd/4"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
RFC_RE = r"[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{2}[0-9A]"
RFC_PUBLICO = "XAXX010101000"
RFC_EXTRANJERO = "XEXX010101000"
UUID_RE = r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"

REGIMEN = tuple((c, c) for c in (
    "601", "603", "605", "606", "607", "608", "609", "610", "611", "612", "614", "615", "616",
    "620", "621", "622", "623", "624", "625", "626", "628", "629", "630"))
USO_CFDI = tuple((c, c) for c in (
    "G01", "G02", "G03", "I01", "I02", "I03", "I04", "I05", "I06", "I07", "I08", "D01", "D02", "D03",
    "D04", "D05", "D06", "D07", "D08", "D09", "D10", "P01", "S01", "CP01", "CN01"))
FORMA_PAGO = (
    ("01", "01 Efectivo"), ("02", "02 Cheque nominativo"), ("03", "03 Transferencia"),
    ("04", "04 Tarjeta de crédito"), ("28", "28 Tarjeta de débito"), ("99", "99 Por definir"),
)
METODO_PAGO = (("PUE", "PUE Pago en una sola exhibición"), ("PPD", "PPD Pago en parcialidades o diferido"))
TRATAMIENTO_CERO = (
    ("tasa0", "IVA tasa 0%"), ("exento", "Exento de IVA"), ("no_objeto", "No objeto de impuesto (01)"),
)
_RATES = {Decimal("16"), Decimal("8")}

_is_mx = lambda doc, p: (p.country_code or "").upper() == "MX"  # noqa: E731
_mx_with_rfc = lambda doc, p: _is_mx(doc, p) and bool((p.tax_id or "").strip())  # noqa: E731
_foreign = lambda doc, p: bool(p.country_code) and not _is_mx(doc, p)  # noqa: E731
_zero = lambda doc, line: Decimal(line.tax_percent) == 0  # noqa: E731


class MxCfdi(NationalFormat):
    mode = "mx_cfdi"
    label = "Mexico - CFDI 4.0 (SAT / PAC)"
    countries = ("MX",)
    xsd = "mx/cfdv40.xsd"
    fields = [
        FieldSpec("seller", "tax_id", "RFC", pattern=RFC_RE),
        FieldSpec("seller", "name", "Nombre / razón social",
                  help="Exactly as registered with SAT (no régimen suffix such as 'S.A. de C.V.')."),
        FieldSpec("seller", "regimen_fiscal", "Régimen fiscal", choices=REGIMEN),
        FieldSpec("seller", "postal_code", "Código postal (LugarExpedicion)", pattern=r"\d{5}"),
        FieldSpec("seller", "forma_pago", "Forma de pago (default)", choices=FORMA_PAGO),
        FieldSpec("seller", "metodo_pago", "Método de pago (default)", choices=METODO_PAGO),
        FieldSpec("seller", "default_clave_prod_serv", "ClaveProdServ (default)", required=False,
                  pattern=r"\d{8}", help="SAT product/service key used for lines without their own."),
        FieldSpec("seller", "default_clave_unidad", "ClaveUnidad (default)", required=False,
                  pattern=r"[A-Z0-9]{1,3}", help="e.g. H87 pieza, E48 unidad de servicio, ACT actividad."),
        FieldSpec("seller", "default_tratamiento_cero", "0% line treatment (default)", required=False,
                  choices=TRATAMIENTO_CERO),
        FieldSpec("buyer", "name", "Nombre / razón social del receptor"),
        FieldSpec("buyer", "country_code", "País del receptor", pattern=r"[A-Z]{2}"),
        FieldSpec("buyer", "tax_id", "RFC del receptor", required=False, pattern=RFC_RE,
                  help="Leave blank for a sale to the general public (XAXX010101000)."),
        FieldSpec("buyer", "postal_code", "Domicilio fiscal (CP)", pattern=r"\d{5}", when=_mx_with_rfc),
        FieldSpec("buyer", "regimen_fiscal", "Régimen fiscal del receptor", choices=REGIMEN, when=_mx_with_rfc),
        FieldSpec("buyer", "uso_cfdi", "Uso del CFDI", choices=USO_CFDI, when=_mx_with_rfc),
        FieldSpec("buyer", "residencia_fiscal", "Residencia fiscal (c_Pais, 3 letras)", pattern=r"[A-Z]{3}",
                  when=_foreign, help="ISO 3166-1 alpha-3, e.g. USA, CAN, ESP."),
        FieldSpec("buyer", "num_reg_id_trib", "Número de registro tributario", when=_foreign),
        FieldSpec("line", "clave_prod_serv", "ClaveProdServ", pattern=r"\d{8}",
                  default_from="default_clave_prod_serv"),
        FieldSpec("line", "clave_unidad", "ClaveUnidad", pattern=r"[A-Z0-9]{1,3}",
                  default_from="default_clave_unidad"),
        FieldSpec("line", "tratamiento_cero", "Tratamiento 0%", choices=TRATAMIENTO_CERO, when=_zero,
                  default_from="default_tratamiento_cero"),
        FieldSpec("document", "tipo_cambio", "Tipo de cambio", pattern=r"\d{1,12}(\.\d{1,6})?",
                  when=lambda doc, _o: (doc.currency or "").upper() != "MXN",
                  help="MXN per 1 unit of the invoice currency (DOF rate)."),
        FieldSpec("document", "forma_pago", "Forma de pago (this invoice)", required=False, choices=FORMA_PAGO),
        FieldSpec("document", "metodo_pago", "Método de pago (this invoice)", required=False, choices=METODO_PAGO),
        FieldSpec("document", "exportacion", "Exportación", required=False,
                  choices=(("01", "01 No aplica"), ("02", "02 Definitiva (A1)"), ("03", "03 Temporal"),
                           ("04", "04 Definitiva con clave distinta a A1"))),
    ]

    # -- validation ---------------------------------------------------------------
    def validate(self, doc: DocInput) -> None:
        problems: list[dict] = []
        try:
            super().validate(doc)
        except EInvoiceDataMissing as exc:
            problems = exc.problems
        for i, line in enumerate(doc.lines, start=1):
            rate = Decimal(line.tax_percent)
            if rate != 0 and rate not in _RATES:
                problems.append({"scope": f"line[{i}]", "key": "tax_percent", "label": "Tasa IVA",
                                 "message": f"{rate}% is not a Mexican IVA rate (16 / 8 / 0)"})
        if doc.is_credit_note and not re.fullmatch(UUID_RE, (doc.get("original_reference") or "").strip()):
            problems.append({"scope": "document", "key": "original_reference", "label": "UUID del CFDI relacionado",
                             "message": "a credit note (Egreso) must relate to the original CFDI's UUID, "
                                        "which is only known once that invoice was stamped"})
        if problems:
            raise EInvoiceDataMissing(self.mode, problems)

    def signing_status(self) -> bool:
        try:
            _csd()
            return True
        except TransportNotConfigured:
            return False

    def signing_problems(self, doc: DocInput) -> list[dict]:
        try:
            _csd()
        except TransportNotConfigured as exc:
            return [{"scope": "seller", "key": "certificate", "label": "CSD (Certificado de Sello Digital)",
                     "message": str(exc)}]
        return []

    # -- build ----------------------------------------------------------------------
    def _line_value(self, key, doc, line):
        return resolve_line_value(next(f for f in self.fields if f.key == key), doc, line)

    def build(self, doc: DocInput) -> str:
        self.validate(doc)
        currency = doc.currency.upper()
        cp = doc.seller.postal_code

        root = ET.Element(f"{{{NS}}}Comprobante", nsmap={"cfdi": NS, "xsi": XSI})
        root.set(f"{{{XSI}}}schemaLocation", f"{NS} http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd")
        a = root.set
        a("Version", "4.0")
        serie, folio = _serie_folio(doc.number)
        if serie:
            a("Serie", serie)
        a("Folio", folio)
        a("Fecha", doc.issue_dt.replace(microsecond=0, tzinfo=None).isoformat())
        a("Sello", "")
        a("NoCertificado", "0" * 20)
        a("Certificado", "")

        metodo = doc.get("metodo_pago") or doc.seller.get("metodo_pago")
        if doc.is_credit_note:
            metodo = "PUE"
        forma = "99" if metodo == "PPD" else (doc.get("forma_pago") or doc.seller.get("forma_pago"))

        # concepts + taxes
        concepts, traslados = [], {}
        subtotal = Decimal("0")
        for line in doc.lines:
            importe = line.net
            subtotal += importe
            rate = Decimal(line.tax_percent)
            treatment = "tasa" if rate > 0 else self._line_value("tratamiento_cero", doc, line)
            objeto = "01" if treatment == "no_objeto" else "02"
            tax = None
            if treatment != "no_objeto":
                factor = "Exento" if treatment == "exento" else "Tasa"
                tasa = (rate / 100).quantize(Decimal("0.000001")) if factor == "Tasa" else None
                imp = (importe * rate / 100).quantize(Decimal("0.01"), ROUND_HALF_UP) if factor == "Tasa" else None
                tax = (factor, tasa, imp)
                key = (factor, tasa)
                base_sum, imp_sum = traslados.get(key, (Decimal("0"), Decimal("0")))
                traslados[key] = (base_sum + importe, imp_sum + (imp or Decimal("0")))
            concepts.append((line, importe, objeto, tax))

        total_tras = sum((v[1] for (factor, _t), v in traslados.items() if factor == "Tasa"), Decimal("0"))
        total = subtotal + total_tras

        a("SubTotal", fmt(subtotal, 2))
        a("Moneda", currency)
        if currency != "MXN":
            a("TipoCambio", str(Decimal(str(doc.get("tipo_cambio")))))
        a("Total", fmt(total, 2))
        a("TipoDeComprobante", "E" if doc.is_credit_note else "I")
        a("Exportacion", doc.get("exportacion") or "01")
        if forma:
            a("FormaPago", forma)
        a("MetodoPago", metodo)
        a("LugarExpedicion", cp)

        # receptor classification
        buyer_rfc = (doc.buyer.tax_id or "").strip().upper()
        foreign = _foreign(doc, doc.buyer)
        publico = not foreign and not buyer_rfc
        if publico:
            ig = ET.SubElement(root, f"{{{NS}}}InformacionGlobal")
            ig.set("Periodicidad", doc.get("periodicidad") or "01")
            ig.set("Meses", f"{doc.issue_dt.month:02d}")
            ig.set("Año", str(doc.issue_dt.year))

        if doc.is_credit_note:
            rel = ET.SubElement(root, f"{{{NS}}}CfdiRelacionados")
            rel.set("TipoRelacion", "01")  # nota de crédito de los documentos relacionados
            ET.SubElement(rel, f"{{{NS}}}CfdiRelacionado").set("UUID", doc.get("original_reference").strip().upper())

        em = ET.SubElement(root, f"{{{NS}}}Emisor")
        em.set("Rfc", doc.seller.tax_id.strip().upper())
        em.set("Nombre", _clean(doc.seller.name, 300))
        em.set("RegimenFiscal", doc.seller.get("regimen_fiscal"))

        rc = ET.SubElement(root, f"{{{NS}}}Receptor")
        if foreign:
            rc.set("Rfc", RFC_EXTRANJERO)
            rc.set("Nombre", _clean(doc.buyer.name, 300))
            rc.set("DomicilioFiscalReceptor", cp)
            rc.set("ResidenciaFiscal", doc.buyer.get("residencia_fiscal"))
            rc.set("NumRegIdTrib", _clean(doc.buyer.get("num_reg_id_trib"), 40))
            rc.set("RegimenFiscalReceptor", "616")
            rc.set("UsoCFDI", "S01")
        elif publico:
            rc.set("Rfc", RFC_PUBLICO)
            rc.set("Nombre", "PUBLICO EN GENERAL")
            rc.set("DomicilioFiscalReceptor", cp)
            rc.set("RegimenFiscalReceptor", "616")
            rc.set("UsoCFDI", "S01")
        else:
            rc.set("Rfc", buyer_rfc)
            rc.set("Nombre", _clean(doc.buyer.name, 300))
            rc.set("DomicilioFiscalReceptor", doc.buyer.postal_code)
            rc.set("RegimenFiscalReceptor", doc.buyer.get("regimen_fiscal"))
            rc.set("UsoCFDI", doc.buyer.get("uso_cfdi"))

        cs = ET.SubElement(root, f"{{{NS}}}Conceptos")
        for line, importe, objeto, tax in concepts:
            c = ET.SubElement(cs, f"{{{NS}}}Concepto")
            c.set("ClaveProdServ", self._line_value("clave_prod_serv", doc, line))
            c.set("Cantidad", _dec(line.quantity, 6))
            c.set("ClaveUnidad", self._line_value("clave_unidad", doc, line))
            c.set("Descripcion", _clean(line.name, 1000) or "-")
            c.set("ValorUnitario", _dec(line.unit_price, 6))
            c.set("Importe", fmt(importe, 2))
            c.set("ObjetoImp", objeto)
            if tax:
                factor, tasa, imp = tax
                ti = ET.SubElement(ET.SubElement(ET.SubElement(c, f"{{{NS}}}Impuestos"), f"{{{NS}}}Traslados"),
                                   f"{{{NS}}}Traslado")
                ti.set("Base", fmt(importe, 2))
                ti.set("Impuesto", "002")
                ti.set("TipoFactor", factor)
                if factor == "Tasa":
                    ti.set("TasaOCuota", str(tasa))
                    ti.set("Importe", fmt(imp, 2))

        if traslados:
            imps = ET.SubElement(root, f"{{{NS}}}Impuestos")
            if any(f == "Tasa" for f, _t in traslados):
                imps.set("TotalImpuestosTrasladados", fmt(total_tras, 2))
            tr = ET.SubElement(imps, f"{{{NS}}}Traslados")
            for (factor, tasa), (base_sum, imp_sum) in sorted(traslados.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
                t = ET.SubElement(tr, f"{{{NS}}}Traslado")
                t.set("Base", fmt(base_sum, 2))
                t.set("Impuesto", "002")
                t.set("TipoFactor", factor)
                if factor == "Tasa":
                    t.set("TasaOCuota", str(tasa))
                    t.set("Importe", fmt(imp_sum, 2))

        return _serialize(root)

    # -- seal -------------------------------------------------------------------------
    def sign(self, document: str, doc: DocInput) -> str:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import Encoding

        key, cert = _csd()
        root = ET.fromstring(document.encode("utf-8"))
        root.set("NoCertificado", no_certificado(cert))
        root.set("Certificado", base64.b64encode(cert.public_bytes(Encoding.DER)).decode("ascii"))
        root.set("Sello", "")
        cadena = cadena_original(root)
        sello = key.sign(cadena.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
        root.set("Sello", base64.b64encode(sello).decode("ascii"))
        return _serialize(root)

    def filename(self, doc: DocInput) -> str:
        serie, folio = _serie_folio(doc.number)
        return f"CFDI_{doc.seller.tax_id.upper()}_{serie}{folio}.xml"

    def client(self):
        return IntermediaryClient("CFDI_PAC", channel_label="PAC (proveedor autorizado de certificación)")


# -- helpers ------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _xslt():
    path = SCHEMAS_DIR / "mx" / "xslt" / "cadenaoriginal_4_0.xslt"
    return ET.XSLT(ET.parse(str(path), ET.XMLParser(no_network=True)))


def cadena_original(root) -> str:
    """SAT's own cadena original transform (Anexo 20), applied offline."""
    return str(_xslt()(ET.ElementTree(root)))


def no_certificado(cert) -> str:
    """SAT encodes the 20-digit certificate number as ASCII in the X.509
    serial, e.g. 0x3330303031... -> '30001...'."""
    raw = format(cert.serial_number, "x")
    raw = raw if len(raw) % 2 == 0 else "0" + raw
    try:
        text = bytes.fromhex(raw).decode("ascii")
    except (ValueError, UnicodeDecodeError):
        text = ""
    if not re.fullmatch(r"\d{20}", text):
        raise TransportNotConfigured("The configured certificate is not a SAT CSD (its serial does not encode "
                                     "a 20-digit certificate number).")
    return text


def _csd():
    import os

    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import load_der_private_key, load_pem_private_key

    from ..signing import KEY_LOADER

    key_bytes, cert_bytes = KEY_LOADER("mx_cfdi")
    if not key_bytes or not cert_bytes:
        raise TransportNotConfigured("No CSD installed. Set CFDI_CSD_PRIVATE_KEY_PATH and CFDI_CSD_CERT_PATH "
                                     "(SAT .key/.cer) and CFDI_CSD_KEY_PASSWORD if the key is encrypted.")
    password = os.getenv("CFDI_CSD_KEY_PASSWORD", "").encode() or None
    try:
        key = (load_pem_private_key(key_bytes, password) if b"-----BEGIN" in key_bytes
               else load_der_private_key(key_bytes, password))
        cert = (x509.load_pem_x509_certificate(cert_bytes) if b"-----BEGIN" in cert_bytes
                else x509.load_der_x509_certificate(cert_bytes))
    except (ValueError, TypeError) as exc:
        raise TransportNotConfigured(f"The CSD could not be loaded: {exc}") from exc
    no_certificado(cert)  # rejects a non-SAT certificate up front
    return key, cert


def _serialize(root) -> str:
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True).decode("utf-8")


def _serie_folio(number: str) -> tuple[str, str]:
    """Split 'INV-2026-0001' into Serie 'INV-2026-' / Folio '0001' when the
    number ends in digits; otherwise the whole number is the Folio."""
    number = (number or "").strip().replace("|", "-")
    m = re.fullmatch(r"(.*?)(\d{1,40})", number)
    if m and m.group(1) and len(m.group(1)) <= 25:
        return m.group(1), m.group(2)
    return "", number[:40]


def _clean(text, limit: int) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().replace("|", "-")[:limit]


def _dec(value, max_places: int) -> str:
    d = Decimal(str(value)).normalize()
    places = min(max_places, max(0, -d.as_tuple().exponent))
    return fmt(d, max(places, 2)) if places else fmt(d, 2)
