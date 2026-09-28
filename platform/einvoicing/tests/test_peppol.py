"""
Peppol BIS Billing 3.0 (EN 16931) builder + engine-mode tests.

The document is the part that's fully ours and fully verifiable without a
commercial Access Point subscription, so that's what's asserted here in
detail: the mandatory CustomizationID/ProfileID that make it Peppol rather
than plain UBL, EN 16931's 2dp amounts (the Gulf profiles use 3dp), and
totals that actually tie to the lines.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal

import pytest

from platform.einvoicing.clients.peppol import PeppolClient, PeppolNotConfigured
from platform.einvoicing.engine import mode_for_country
from platform.einvoicing.ubl import (
    PeppolInvoiceData,
    PeppolParty,
    UblLine,
    build_peppol_ubl,
)

CBC = "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
CAC = "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"


def _invoice(**kw):
    defaults = dict(
        number="INV-2026-001",
        issue_dt=datetime(2026, 3, 1, 10, 30),
        currency="EUR",
        seller=PeppolParty(
            tin="DE123456789", name="Cycom GmbH", country_code="DE",
            city="Berlin", street="Hauptstr 1",
            endpoint_id="DE123456789", endpoint_scheme="9930",
        ),
        buyer=PeppolParty(
            tin="NL987654321", name="Klant BV", country_code="NL",
            city="Amsterdam", endpoint_id="NL987654321", endpoint_scheme="9930",
        ),
        lines=[
            UblLine(line_id="1", name="Consulting", quantity=Decimal("10"),
                    unit_price=Decimal("100.00"), tax_percent=Decimal("19")),
            UblLine(line_id="2", name="Licence", quantity=Decimal("2"),
                    unit_price=Decimal("50.00"), tax_percent=Decimal("19")),
        ],
    )
    defaults.update(kw)
    return PeppolInvoiceData(**defaults)


def test_document_is_identifiably_peppol_not_just_ubl():
    root = ET.fromstring(build_peppol_ubl(_invoice()))
    customization = root.find(f"{CBC}CustomizationID").text
    profile = root.find(f"{CBC}ProfileID").text
    assert customization == (
        "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
    )
    assert profile == "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"


def test_totals_tie_to_the_lines():
    root = ET.fromstring(build_peppol_ubl(_invoice()))
    lmt = root.find(f"{CAC}LegalMonetaryTotal")
    # 10*100 + 2*50 = 1100 net; 19% = 209; gross 1309
    assert lmt.find(f"{CBC}LineExtensionAmount").text == "1100.00"
    assert lmt.find(f"{CBC}TaxExclusiveAmount").text == "1100.00"
    assert lmt.find(f"{CBC}TaxInclusiveAmount").text == "1309.00"
    assert lmt.find(f"{CBC}PayableAmount").text == "1309.00"
    assert root.find(f"{CAC}TaxTotal/{CBC}TaxAmount").text == "209.00"


def test_amounts_are_two_decimal_places_per_en16931():
    """The JO/SA builders emit 3dp; EN 16931 wants 2dp. A Peppol document
    carrying 3dp amounts fails Schematron at the Access Point."""
    root = ET.fromstring(build_peppol_ubl(_invoice()))
    for el in root.iter():
        if el.tag.endswith("Amount") and el.text:
            assert len(el.text.split(".")[-1]) == 2, f"{el.tag}={el.text}"


def test_endpoint_ids_are_emitted_with_their_scheme():
    """EndpointID is what actually routes the document on the network --
    without schemeID the receiving AP can't resolve the participant."""
    root = ET.fromstring(build_peppol_ubl(_invoice()))
    supplier = root.find(f"{CAC}AccountingSupplierParty/{CAC}Party")
    endpoint = supplier.find(f"{CBC}EndpointID")
    assert endpoint.text == "DE123456789"
    assert endpoint.get("schemeID") == "9930"


def test_zero_rated_line_is_category_Z_not_S():
    inv = _invoice(lines=[
        UblLine(line_id="1", name="Export", quantity=Decimal("1"),
                unit_price=Decimal("500.00"), tax_percent=Decimal("0")),
    ])
    root = ET.fromstring(build_peppol_ubl(inv))
    cat = root.find(f"{CAC}TaxTotal/{CAC}TaxSubtotal/{CAC}TaxCategory/{CBC}ID")
    assert cat.text == "Z"
    assert root.find(f"{CAC}TaxTotal/{CBC}TaxAmount").text == "0.00"


def test_mixed_rates_produce_one_subtotal_each():
    inv = _invoice(lines=[
        UblLine(line_id="1", name="Standard", quantity=Decimal("1"),
                unit_price=Decimal("100.00"), tax_percent=Decimal("21")),
        UblLine(line_id="2", name="Reduced", quantity=Decimal("1"),
                unit_price=Decimal("100.00"), tax_percent=Decimal("9")),
    ])
    root = ET.fromstring(build_peppol_ubl(inv))
    subtotals = root.findall(f"{CAC}TaxTotal/{CAC}TaxSubtotal")
    assert len(subtotals) == 2
    assert root.find(f"{CAC}TaxTotal/{CBC}TaxAmount").text == "30.00"


def test_buyer_reference_and_due_date_are_optional_but_emitted_when_set():
    from datetime import date
    root = ET.fromstring(build_peppol_ubl(_invoice()))
    assert root.find(f"{CBC}BuyerReference") is None
    assert root.find(f"{CBC}DueDate") is None

    root2 = ET.fromstring(build_peppol_ubl(
        _invoice(buyer_reference="PO-4412", due_date=date(2026, 4, 1))
    ))
    assert root2.find(f"{CBC}BuyerReference").text == "PO-4412"
    assert root2.find(f"{CBC}DueDate").text == "2026-04-01"


# ── mode routing ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("country", ["DE", "NL", "FR", "SE", "AE", "GB", "NO", "AU", "SG"])
def test_peppol_countries_route_to_the_peppol_mode(country):
    assert mode_for_country(country) == "eu_peppol"


def test_gulf_national_mandates_keep_their_own_modes():
    assert mode_for_country("JO") == "jo_jofotara"
    assert mode_for_country("SA") == "sa_zatca"


@pytest.mark.parametrize("country,mode", [
    ("IT", "it_fatturapa"),
    ("PL", "pl_ksef"),
])
def test_national_formats_outside_peppol_route_to_their_own_mode(country, mode):
    """IT SdI, PL KSeF, MX CFDI and BR NF-e are national formats, NOT
    Peppol. Mapping them to Peppol would generate a document their tax
    authority rejects -- they route to their own national builder."""
    assert mode_for_country(country) == mode


# ── transport seam ─────────────────────────────────────────────────────────

def test_unconfigured_access_point_refuses_instead_of_faking_success(monkeypatch):
    monkeypatch.delenv("PEPPOL_AP_BASE_URL", raising=False)
    monkeypatch.delenv("PEPPOL_AP_API_KEY", raising=False)
    client = PeppolClient()
    assert client.configured is False
    with pytest.raises(PeppolNotConfigured):
        client.submit("<Invoice/>", sender_id="a", receiver_id="b", doc_id="1")


def test_client_reports_configured_when_env_is_set(monkeypatch):
    monkeypatch.setenv("PEPPOL_AP_BASE_URL", "https://ap.example.com")
    monkeypatch.setenv("PEPPOL_AP_API_KEY", "key-123")
    assert PeppolClient().configured is True
