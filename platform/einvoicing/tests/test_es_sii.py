"""
SII (Spain) libro de facturas expedidas tests. Every record is validated
against the AEAT SII 1.1 XSDs vendored under schemas/es/.
"""
from datetime import date, datetime
from decimal import Decimal

import pytest
from lxml import etree

from platform.einvoicing.national import EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.national.base import DocInput, LineInput, PartyInput
from platform.einvoicing.national.es_sii import LR, SII, EsSii, nif_valid

FMT = EsSii()


def _seller(**extra):
    return PartyInput(tax_id="B12345674", name="CYCOM ESPAÑA SL", country_code="ES",
                      extra={"sii_obligado": "S", "clave_regimen": "01",
                             "descripcion_operacion": "Venta de mercaderías y servicios", **extra})


def _buyer(**kw):
    base = dict(tax_id="12345678Z", name="CLIENTE NACIONAL SL", country_code="ES")
    base.update(kw)
    return PartyInput(**base)


def _doc(**kw):
    base = dict(number="FV-2026-0001", issue_dt=datetime(2026, 9, 3, 9, 0), currency="EUR",
                seller=_seller(), buyer=_buyer(),
                lines=[LineInput("Consultoría", Decimal("10"), Decimal("100"), Decimal("21")),
                       LineInput("Libros", Decimal("5"), Decimal("20"), Decimal("4"))])
    base.update(kw)
    return DocInput(**base)


def _x(xml, path):
    """path of (ns, tag) pairs joined by '/': 'lr:Registro.../sii:...'"""
    root = etree.fromstring(xml.encode())
    return root.xpath(path, namespaces={"lr": LR, "sii": SII})


def test_nif_validation():
    assert nif_valid("B12345674")       # CIF
    assert nif_valid("12345678Z")       # DNI
    assert nif_valid("X1234567L")       # NIE
    assert not nif_valid("12345678A")
    assert not nif_valid("B12345675")


def test_domestic_invoice_is_valid_against_the_aeat_xsd():
    xml = FMT.build(_doc())
    assert FMT.schema_errors(xml) == []
    assert _x(xml, "string(//sii:IDVersionSii)") == "1.1"
    assert _x(xml, "string(//lr:FacturaExpedida/sii:TipoFactura)") == "F1"
    assert _x(xml, "string(//sii:PeriodoLiquidacion/sii:Periodo)") == "09"
    assert _x(xml, "string(//sii:FechaExpedicionFacturaEmisor)") == "03-09-2026"


def test_vat_breakdown_per_rate_and_total():
    xml = FMT.build(_doc())
    rows = [(r.xpath("string(sii:TipoImpositivo)", namespaces={"sii": SII}),
             r.xpath("string(sii:BaseImponible)", namespaces={"sii": SII}),
             r.xpath("string(sii:CuotaRepercutida)", namespaces={"sii": SII}))
            for r in _x(xml, "//sii:DetalleIVA")]
    assert rows == [("4", "100.00", "4.00"), ("21", "1000.00", "210.00")]
    assert _x(xml, "string(//sii:ImporteTotal)") == "1314.00"
    assert _x(xml, "string(//sii:TipoNoExenta)") == "S1"


def test_zero_rated_lines_need_a_reason_and_exempt_ones_a_cause():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(lines=[LineInput("Formación", Decimal("1"), Decimal("500"), Decimal("0"))]))
    assert any(p["key"] == "tratamiento_cero" for p in exc.value.problems)
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(lines=[LineInput("Formación", Decimal("1"), Decimal("500"), Decimal("0"),
                                        extra={"tratamiento_cero": "exenta"})]))
    assert any(p["key"] == "causa_exencion" for p in exc.value.problems)


def test_exempt_isp_and_not_subject_lines():
    lines = [
        LineInput("Servicio", Decimal("1"), Decimal("1000"), Decimal("21")),
        LineInput("Formación", Decimal("1"), Decimal("500"), Decimal("0"),
                  extra={"tratamiento_cero": "exenta", "causa_exencion": "E1"}),
        LineInput("Chatarra", Decimal("1"), Decimal("300"), Decimal("0"), extra={"tratamiento_cero": "isp"}),
        LineInput("Indemnización", Decimal("1"), Decimal("50"), Decimal("0"),
                  extra={"tratamiento_cero": "no_sujeta_art7_14"}),
    ]
    xml = FMT.build(_doc(lines=lines))
    assert FMT.schema_errors(xml) == []
    assert _x(xml, "string(//sii:DetalleExenta/sii:CausaExencion)") == "E1"
    assert _x(xml, "string(//sii:TipoNoExenta)") == "S3"            # S1 + S2 together
    assert _x(xml, "string(//sii:ImportePorArticulos7_14_Otros)") == "50.00"


def test_foreign_eu_customer_uses_idotro_and_operation_type_breakdown():
    doc = _doc(buyer=PartyInput(tax_id="DE123456789", name="Kunde GmbH", country_code="DE"),
               lines=[LineInput("Software", Decimal("1"), Decimal("2000"), Decimal("0"),
                                extra={"tratamiento_cero": "no_sujeta_localizacion", "tipo_operacion": "servicio"}),
                      LineInput("Equipo", Decimal("1"), Decimal("800"), Decimal("0"),
                                extra={"tratamiento_cero": "exenta", "causa_exencion": "E5",
                                       "tipo_operacion": "entrega"})])
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    assert _x(xml, "string(//sii:IDOtro/sii:IDType)") == "02"
    assert _x(xml, "string(//sii:IDOtro/sii:CodigoPais)") == "DE"
    assert _x(xml, "string(//sii:PrestacionServicios//sii:ImporteTAIReglasLocalizacion)") == "2000.00"
    assert _x(xml, "string(//sii:Entrega//sii:CausaExencion)") == "E5"


def test_rectificativa_por_diferencias():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(is_credit_note=True, original_number="FV-2026-0001"))
    assert any(p["key"] == "tipo_rectificativa" for p in exc.value.problems)
    xml = FMT.build(_doc(is_credit_note=True, number="R-2026-0001", original_number="FV-2026-0001",
                         original_date=date(2026, 9, 3), extra={"tipo_rectificativa": "R1"}))
    assert FMT.schema_errors(xml) == []
    assert _x(xml, "string(//lr:FacturaExpedida/sii:TipoFactura)") == "R1"
    assert _x(xml, "string(//sii:TipoRectificativa)") == "I"
    assert _x(xml, "string(//sii:ImporteTotal)") == "-1314.00"
    assert _x(xml, "string(//sii:IDFacturaRectificada/sii:NumSerieFacturaEmisor)") == "FV-2026-0001"


def test_non_sii_taxpayer_is_not_applicable():
    assert FMT.not_applicable_reason(_doc(seller=_seller(sii_obligado="N")))
    assert FMT.not_applicable_reason(_doc()) is None


def test_bad_nif_and_rate_refused():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(buyer=_buyer(tax_id="12345678A"),
                       lines=[LineInput("x", Decimal("1"), Decimal("1"), Decimal("19"))]))
    keys = {(p["scope"], p["key"]) for p in exc.value.problems}
    assert ("buyer", "tax_id") in keys and ("line[1]", "tax_percent") in keys


def test_schema_check_is_real():
    xml = FMT.build(_doc())
    assert FMT.schema_errors(xml.replace(">F1<", ">F9<"))


def test_unconfigured_gateway_refuses(monkeypatch):
    monkeypatch.delenv("SII_BASE_URL", raising=False)
    with pytest.raises(TransportNotConfigured):
        FMT.submit("<x/>", _doc())
