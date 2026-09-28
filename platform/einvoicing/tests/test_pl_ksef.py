"""
KSeF FA(3) (Poland) builder tests. Every document is validated against the
Ministry of Finance FA(3) XSD vendored under schemas/pl/.
"""
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from platform.einvoicing.national import EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.national.base import SCHEMAS_DIR, DocInput, LineInput, PartyInput
from platform.einvoicing.national.pl_ksef import PlKsef, nip_valid

FMT = PlKsef()
NS = "{http://crd.gov.pl/wzor/2025/06/25/13775/}"
SELLER_NIP = "5260250274"   # checksum-valid
BUYER_NIP = "1234563218"    # checksum-valid


def _seller(**extra):
    return PartyInput(tax_id=SELLER_NIP, name="Cycom Polska Sp. z o.o.", street="ul. Marszałkowska",
                      building_number="1", postal_code="00-001", city="Warszawa", country_code="PL",
                      extra={"metoda_kasowa": "2", **extra})


def _buyer(**kw):
    base = dict(tax_id=BUYER_NIP, name="Klient S.A.", street="ul. Długa 5", postal_code="30-001",
                city="Kraków", country_code="PL")
    base.update(kw)
    return PartyInput(**base)


def _doc(**kw):
    base = dict(
        number="FV/2026/09/001", issue_dt=datetime(2026, 9, 1, 10, 0), currency="PLN",
        seller=_seller(), buyer=_buyer(), due_date=date(2026, 9, 15),
        lines=[
            LineInput("Usługa doradcza", Decimal("10"), Decimal("100.00"), Decimal("23")),
            LineInput("Książka", Decimal("2"), Decimal("50.00"), Decimal("5")),
        ],
    )
    base.update(kw)
    return DocInput(**base)


def _find(xml, path):
    return ET.fromstring(xml).find("/".join(f"{NS}{p}" for p in path.split("/")))


def test_every_vendored_schema_is_offline():
    """No remote schemaLocation anywhere -- validation must not depend on
    (or silently fetch from) a government server at runtime."""
    for xsd in Path(SCHEMAS_DIR).rglob("*.xsd"):
        remote = re.findall(r'schemaLocation="(https?://[^"]+)"', xsd.read_text(encoding="utf-8"))
        assert not remote, f"{xsd.name} still imports {remote}"


def test_nip_checksum():
    assert nip_valid(SELLER_NIP) and nip_valid(BUYER_NIP)
    assert not nip_valid("5260250275")


def test_standard_invoice_is_valid_against_the_fa3_xsd():
    xml = FMT.build(_doc())
    assert FMT.schema_errors(xml) == []
    assert _find(xml, "Fa/RodzajFaktury").text == "VAT"
    assert _find(xml, "Naglowek/KodFormularza").get("kodSystemowy") == "FA (3)"


def test_rate_buckets_and_total():
    xml = FMT.build(_doc())
    # 23%: 1000 net / 230 tax ; 5%: 100 net / 5 tax ; gross 1335
    assert _find(xml, "Fa/P_13_1").text == "1000.00"
    assert _find(xml, "Fa/P_14_1").text == "230.00"
    assert _find(xml, "Fa/P_13_3").text == "100.00"
    assert _find(xml, "Fa/P_14_3").text == "5.00"
    assert _find(xml, "Fa/P_15").text == "1335.00"
    assert _find(xml, "Fa/Adnotacje/Zwolnienie/P_19N").text == "1"


def test_zero_rated_line_needs_its_legal_basis():
    doc = _doc(lines=[LineInput("Eksport", Decimal("1"), Decimal("500"), Decimal("0"))])
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(doc)
    assert any(p["key"] == "stawka_zero" for p in exc.value.problems)


def test_zero_rated_buckets_by_basis_and_exemption_needs_its_legal_basis_text():
    lines = [
        LineInput("Eksport", Decimal("1"), Decimal("500"), Decimal("0"), extra={"stawka_zero": "0 EX"}),
        LineInput("Usługa medyczna", Decimal("1"), Decimal("200"), Decimal("0"), extra={"stawka_zero": "zw"}),
        LineInput("Odwrotne", Decimal("1"), Decimal("300"), Decimal("0"), extra={"stawka_zero": "oo"}),
    ]
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(lines=lines))
    assert any(p["key"] == "zwolnienie_podstawa" for p in exc.value.problems)

    doc = _doc(lines=lines, seller=_seller(zwolnienie_podstawa="art. 43 ust. 1 pkt 18 ustawy o VAT"))
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    assert _find(xml, "Fa/P_13_6_3").text == "500.00"
    assert _find(xml, "Fa/P_13_7").text == "200.00"
    assert _find(xml, "Fa/P_13_10").text == "300.00"
    assert _find(xml, "Fa/Adnotacje/P_18").text == "1"           # reverse charge flagged
    assert _find(xml, "Fa/Adnotacje/Zwolnienie/P_19A").text.startswith("art. 43")


def test_foreign_currency_needs_the_nbp_rate_and_reports_vat_in_pln():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(currency="EUR"))
    assert any(p["key"] == "kurs_waluty" for p in exc.value.problems)

    xml = FMT.build(_doc(currency="EUR", extra={"kurs_waluty": "4.2512"}))
    assert FMT.schema_errors(xml) == []
    assert _find(xml, "Fa/P_14_1W").text == "977.78"   # 230 * 4.2512


def test_eu_buyer_is_identified_by_vat_ue_and_consumer_by_brakid():
    eu = FMT.build(_doc(buyer=_buyer(tax_id="DE123456789", country_code="DE", city="Berlin", postal_code="10115")))
    assert FMT.schema_errors(eu) == []
    assert _find(eu, "Podmiot2/DaneIdentyfikacyjne/KodUE").text == "DE"
    assert _find(eu, "Podmiot2/DaneIdentyfikacyjne/NrVatUE").text == "123456789"

    b2c = FMT.build(_doc(buyer=_buyer(tax_id="", name="Jan Kowalski")))
    assert FMT.schema_errors(b2c) == []
    assert _find(b2c, "Podmiot2/DaneIdentyfikacyjne/BrakID").text == "1"


def test_correction_is_kor_with_negative_differences():
    doc = _doc(is_credit_note=True, original_number="FV/2026/08/077", original_date=date(2026, 8, 20),
               number="KOR/2026/09/001",
               extra={"original_reference": f"{SELLER_NIP}-20260820-0A1B2C-3D4E5F-A7"})
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    assert _find(xml, "Fa/RodzajFaktury").text == "KOR"
    assert _find(xml, "Fa/P_15").text == "-1335.00"
    assert _find(xml, "Fa/DaneFaKorygowanej/NrKSeFFaKorygowanej").text.startswith(SELLER_NIP)


def test_correction_of_an_invoice_issued_outside_ksef():
    doc = _doc(is_credit_note=True, original_number="FV/2025/12/001", original_date=date(2025, 12, 1))
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    assert _find(xml, "Fa/DaneFaKorygowanej/NrKSeFN").text == "1"


def test_invalid_nip_and_non_polish_rate_are_refused():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(seller=PartyInput(tax_id="5260250275", name="X", street="a", postal_code="00-001",
                                         city="W", country_code="PL", extra={"metoda_kasowa": "2"}),
                       lines=[LineInput("x", Decimal("1"), Decimal("1"), Decimal("19"))]))
    keys = {p["key"] for p in exc.value.problems}
    assert {"tax_id", "tax_percent"} <= keys


def test_payment_block():
    xml = FMT.build(_doc(seller=_seller(forma_platnosci="6", iban="PL61109010140000071219812874")))
    assert FMT.schema_errors(xml) == []
    assert _find(xml, "Fa/Platnosc/FormaPlatnosci").text == "6"
    assert _find(xml, "Fa/Platnosc/TerminPlatnosci/Termin").text == "2026-09-15"


def test_schema_check_is_real():
    xml = FMT.build(_doc())
    assert FMT.schema_errors(xml.replace("<P_12>23</P_12>", "<P_12>19</P_12>"))


def test_unconfigured_transport_refuses(monkeypatch):
    monkeypatch.delenv("KSEF_BASE_URL", raising=False)
    with pytest.raises(TransportNotConfigured):
        FMT.submit("<x/>", _doc())
