"""
FatturaPA (Italy / SdI) builder tests.

Every generated document is validated against the official Agenzia delle
Entrate XSD (v1.2.2, vendored under schemas/it/) -- structural conformance
is asserted by the real schema, not by hand-picked XPath spot checks. The
business rules SdI enforces beyond the XSD (per-summary tax, Natura on
zero-rated lines, foreign-address conventions) are asserted directly.
"""
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal

import pytest

from platform.einvoicing.national import FORMATS, EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.national.base import DocInput, LineInput, PartyInput
from platform.einvoicing.national.it_fatturapa import ItFatturaPA
from platform.einvoicing.tests.test_signing import _self_signed

FMT = ItFatturaPA()
NS = "{http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2}"


def _seller(**kw):
    base = dict(
        tax_id="01234567890", name="Cycom Italia S.r.l.", street="Via Roma", building_number="10",
        city="Milano", postal_code="20121", region="MI", country_code="IT",
        extra={"regime_fiscale": "RF01"},
    )
    base.update(kw)
    return PartyInput(**base)


def _buyer(**kw):
    base = dict(
        tax_id="IT09876543210", name="Cliente S.p.A.", street="Corso Italia 5", city="Torino",
        postal_code="10121", country_code="IT", extra={"codice_destinatario": "ABC1234"},
    )
    base.update(kw)
    return PartyInput(**base)


def _doc(**kw):
    base = dict(
        number="FT-2026-0001", issue_dt=datetime(2026, 9, 1, 10, 0), currency="EUR",
        seller=_seller(), buyer=_buyer(), icv=1,
        lines=[
            LineInput("Consulenza", Decimal("10"), Decimal("100.00"), Decimal("22")),
            LineInput("Licenza", Decimal("3"), Decimal("33.33"), Decimal("22")),
        ],
    )
    base.update(kw)
    return DocInput(**base)


def _root(xml):
    return ET.fromstring(xml)


def test_registered_for_italy():
    assert FORMATS["it_fatturapa"].countries == ("IT",)


def test_standard_b2b_invoice_is_valid_against_the_official_xsd():
    xml = FMT.build(_doc())
    assert FMT.schema_errors(xml) == []
    root = _root(xml)
    assert root.get("versione") == "FPR12"
    assert root.find("FatturaElettronicaHeader/DatiTrasmissione/CodiceDestinatario").text == "ABC1234"
    assert root.find("FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/TipoDocumento").text == "TD01"


def test_summary_tax_is_computed_per_rate_group_and_totals_tie():
    root = _root(FMT.build(_doc()))
    # 1000 + 99.99 = 1099.99 taxable; 22% of the GROUP = 241.9978 -> 242.00
    # (summing per-line tax would give 220.00 + 22.00 = 242.00 here too, but
    # SdI checks the group product, so that's what we compute)
    rie = root.find("FatturaElettronicaBody/DatiBeniServizi/DatiRiepilogo")
    assert rie.find("ImponibileImporto").text == "1099.99"
    assert rie.find("Imposta").text == "242.00"
    total = root.find("FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/ImportoTotaleDocumento")
    assert total.text == "1341.99"


def test_schema_check_is_real_a_corrupted_document_fails_it():
    """Negative control: proves schema_errors() isn't vacuously passing."""
    xml = FMT.build(_doc())
    assert FMT.schema_errors(xml.replace("<CAP>20121</CAP>", "<CAP>2O121</CAP>"))
    assert FMT.schema_errors(xml.replace("<RegimeFiscale>RF01</RegimeFiscale>", "<RegimeFiscale>RF99</RegimeFiscale>"))
    assert FMT.schema_errors(xml.replace("<Descrizione>Licenza</Descrizione>", "<Descrizione>خدمة</Descrizione>"))


def test_zero_rated_line_without_natura_is_refused_not_guessed():
    doc = _doc(lines=[LineInput("Export", Decimal("1"), Decimal("500"), Decimal("0"))])
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(doc)
    assert any(p["key"] == "natura" for p in exc.value.problems)


def test_zero_rated_line_uses_its_natura_or_the_seller_default():
    doc = _doc(
        seller=_seller(extra={"regime_fiscale": "RF01", "default_natura": "N3.1"}),
        lines=[
            LineInput("Export", Decimal("1"), Decimal("500"), Decimal("0")),
            LineInput("Esente", Decimal("1"), Decimal("100"), Decimal("0"), extra={"natura": "N4"}),
            LineInput("Standard", Decimal("1"), Decimal("100"), Decimal("22")),
        ],
    )
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    rie = _root(xml).findall("FatturaElettronicaBody/DatiBeniServizi/DatiRiepilogo")
    got = {(r.find("AliquotaIVA").text, getattr(r.find("Natura"), "text", None)) for r in rie}
    assert got == {("0.00", "N3.1"), ("0.00", "N4"), ("22.00", None)}


def test_missing_regime_and_sdi_code_are_all_reported_at_once():
    doc = _doc(seller=_seller(extra={}), buyer=_buyer(extra={}))
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(doc)
    keys = {(p["scope"], p["key"]) for p in exc.value.problems}
    assert {("seller", "regime_fiscale"), ("buyer", "codice_destinatario")} <= keys


def test_foreign_buyer_uses_the_sdi_conventions():
    doc = _doc(buyer=PartyInput(tax_id="DE123456789", name="Kunde GmbH", street="Hauptstr 1",
                                city="Berlin", postal_code="10115", country_code="DE"))
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    root = _root(xml)
    assert root.find("FatturaElettronicaHeader/DatiTrasmissione/CodiceDestinatario").text == "XXXXXXX"
    ces = root.find("FatturaElettronicaHeader/CessionarioCommittente")
    assert ces.find("DatiAnagrafici/IdFiscaleIVA/IdPaese").text == "DE"
    assert ces.find("DatiAnagrafici/IdFiscaleIVA/IdCodice").text == "123456789"
    assert ces.find("Sede/CAP").text == "00000"


def test_credit_note_is_td04_and_references_the_original():
    doc = _doc(is_credit_note=True, original_number="FT-2026-0001", original_date=date(2026, 9, 1),
               number="NC-2026-0001")
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    dg = _root(xml).find("FatturaElettronicaBody/DatiGenerali")
    assert dg.find("DatiGeneraliDocumento/TipoDocumento").text == "TD04"
    assert dg.find("DatiFattureCollegate/IdDocumento").text == "FT-2026-0001"


def test_credit_note_without_original_is_refused():
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(is_credit_note=True))


def test_number_without_a_digit_is_refused():
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(number="ABC"))


def test_public_administration_buyer_is_fpa12():
    doc = _doc(buyer=_buyer(extra={"codice_destinatario": "UFABCD"}))
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    assert _root(xml).get("versione") == "FPA12"


def test_payment_block_when_configured_and_due_date_set():
    doc = _doc(
        seller=_seller(extra={"regime_fiscale": "RF01", "modalita_pagamento": "MP05",
                              "iban": "IT60X0542811101000000123456"}),
        due_date=date(2026, 10, 1),
    )
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    det = _root(xml).find("FatturaElettronicaBody/DatiPagamento/DettaglioPagamento")
    assert det.find("ModalitaPagamento").text == "MP05"
    assert det.find("ImportoPagamento").text == "1341.99"


def test_filename_follows_sdi_naming():
    assert FMT.filename(_doc(icv=37)) == "IT01234567890_00011.xml"


def test_non_latin_text_is_made_schema_safe():
    doc = _doc(lines=[LineInput("خدمة استشارية", Decimal("1"), Decimal("10"), Decimal("22"))])
    assert FMT.schema_errors(FMT.build(doc)) == []


def test_b2b_without_a_key_is_sent_unsigned_but_pa_refuses(monkeypatch):
    monkeypatch.delenv("FATTURAPA_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("FATTURAPA_CERT_PATH", raising=False)
    b2b = FMT.build(_doc())
    assert FMT.sign(b2b, _doc()) == b2b
    pa_doc = _doc(buyer=_buyer(extra={"codice_destinatario": "UFABCD"}))
    with pytest.raises(TransportNotConfigured):
        FMT.sign(FMT.build(pa_doc), pa_doc)


def test_signed_document_still_validates_against_the_xsd(tmp_path, monkeypatch):
    key_pem, cert_pem = _self_signed()
    (tmp_path / "k.pem").write_bytes(key_pem)
    (tmp_path / "c.pem").write_bytes(cert_pem)
    monkeypatch.setenv("FATTURAPA_PRIVATE_KEY_PATH", str(tmp_path / "k.pem"))
    monkeypatch.setenv("FATTURAPA_CERT_PATH", str(tmp_path / "c.pem"))
    signed = FMT.sign(FMT.build(_doc()), _doc())
    assert "Signature" in signed
    assert FMT.schema_errors(signed) == []


def test_unconfigured_transport_refuses(monkeypatch):
    monkeypatch.delenv("SDI_BASE_URL", raising=False)
    monkeypatch.delenv("SDI_API_KEY", raising=False)
    with pytest.raises(TransportNotConfigured):
        FMT.submit("<x/>", _doc())
