"""
GST e-invoice (India, INV-01 v1.1) builder tests. Every payload is
validated against the IRP v1.1 JSON Schema under schemas/in/.
"""
import json
from datetime import date, datetime
from decimal import Decimal

import pytest

from platform.einvoicing.national import EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.national.base import DocInput, LineInput, PartyInput
from platform.einvoicing.national.in_gst import _CHARS, InGst, gstin_valid

FMT = InGst()


def _gstin(prefix14: str) -> str:
    total = 0
    for i, ch in enumerate(prefix14):
        product = _CHARS.index(ch) * (2 if i % 2 else 1)
        total += product // 36 + product % 36
    return prefix14 + _CHARS[(36 - total % 36) % 36]


SELLER = _gstin("29AABCC1234D1Z")     # Karnataka
BUYER_KA = _gstin("29AAACX9876P1Z")   # Karnataka (intra-state)
BUYER_MH = _gstin("27AAACY5555Q1Z")   # Maharashtra (inter-state)


def _seller(**extra):
    return PartyInput(tax_id=SELLER, name="Cycom India Pvt Ltd", street="100 MG Road", city="Bengaluru",
                      postal_code="560001", country_code="IN",
                      extra={"default_hsn": "998314", "default_unit": "NOS", **extra})


def _buyer(gstin=BUYER_MH, **kw):
    base = dict(tax_id=gstin, name="Buyer Industries Ltd", street="Nariman Point", city="Mumbai",
                postal_code="400021", country_code="IN")
    base.update(kw)
    return PartyInput(**base)


def _doc(**kw):
    base = dict(number="INV/2026/0001", issue_dt=datetime(2026, 9, 1, 10, 0), currency="INR",
                seller=_seller(), buyer=_buyer(),
                lines=[LineInput("IT consulting", Decimal("10"), Decimal("1000.00"), Decimal("18")),
                       LineInput("Laptop", Decimal("1"), Decimal("50000.00"), Decimal("18"),
                                 extra={"hsn": "84713010"})])
    base.update(kw)
    return DocInput(**base)


def _p(doc):
    return json.loads(FMT.build(doc))


def test_gstin_checksum():
    assert gstin_valid("27AAPFU0939F1ZV")          # widely published valid example
    assert not gstin_valid("27AAPFU0939F1ZW")
    assert gstin_valid(SELLER)


def test_inter_state_b2b_uses_igst_and_is_schema_valid():
    doc = _doc()
    assert FMT.schema_errors(FMT.build(doc)) == []
    p = _p(doc)
    assert p["TranDtls"]["SupTyp"] == "B2B"
    assert p["BuyerDtls"]["Pos"] == "27"
    v = p["ValDtls"]
    # 10000 + 50000 = 60000 ; IGST 18% = 10800
    assert (v["AssVal"], v["IgstVal"], v["CgstVal"], v["TotInvVal"]) == (60000.0, 10800.0, 0.0, 70800.0)
    assert p["ItemList"][0]["IsServc"] == "Y" and "Unit" not in p["ItemList"][0]   # SAC 99xxxx
    assert p["ItemList"][1]["IsServc"] == "N" and p["ItemList"][1]["Unit"] == "NOS"


def test_intra_state_splits_cgst_and_sgst():
    p = _p(_doc(buyer=_buyer(BUYER_KA, city="Mysuru", postal_code="570001")))
    v = p["ValDtls"]
    assert (v["CgstVal"], v["SgstVal"], v["IgstVal"]) == (5400.0, 5400.0, 0.0)


def test_b2c_is_not_applicable_rather_than_incomplete():
    doc = _doc(buyer=_buyer(gstin=""))
    assert FMT.not_applicable_reason(doc)


def test_export_without_payment():
    doc = _doc(buyer=PartyInput(name="ACME Inc", street="1 Main St", city="New York", country_code="US"),
               currency="USD",
               lines=[LineInput("Software services", Decimal("1"), Decimal("5000"), Decimal("0"))])
    xml = FMT.build(doc)
    assert FMT.schema_errors(xml) == []
    p = json.loads(xml)
    assert p["TranDtls"]["SupTyp"] == "EXPWOP"
    assert (p["BuyerDtls"]["Gstin"], p["BuyerDtls"]["Pos"], p["BuyerDtls"]["Pin"]) == ("URP", "96", 999999)
    assert p["ExpDtls"] == {"CntCode": "US", "ForCur": "USD"}


def test_sez_with_payment_uses_igst_even_in_the_same_state():
    p = _p(_doc(buyer=_buyer(BUYER_KA, extra={"sez": "Y"})))
    assert p["TranDtls"]["SupTyp"] == "SEZWP"
    assert p["ValDtls"]["IgstVal"] == 10800.0


def test_credit_note_references_the_original():
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(is_credit_note=True))
    xml = FMT.build(_doc(is_credit_note=True, number="CN/2026/0001", original_number="INV/2026/0001",
                         original_date=date(2026, 9, 1)))
    assert FMT.schema_errors(xml) == []
    p = json.loads(xml)
    assert p["DocDtls"]["Typ"] == "CRN"
    assert p["RefDtls"]["PrecDocDtls"][0] == {"InvNo": "INV/2026/0001", "InvDt": "01/09/2026"}


def test_irp_document_number_rules():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(number="inv-2026-000000001"))
    assert any(p["key"] == "number" for p in exc.value.problems)


def test_invalid_gstin_and_rate_refused():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(buyer=_buyer("27AAPFU0939F1ZW"),
                       lines=[LineInput("x", Decimal("1"), Decimal("1"), Decimal("16"))]))
    keys = {(p["scope"], p["key"]) for p in exc.value.problems}
    assert ("buyer", "tax_id") in keys and ("line[1]", "tax_percent") in keys


def test_goods_line_needs_a_unit():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(seller=_seller(default_unit=""),
                       lines=[LineInput("Laptop", Decimal("1"), Decimal("1"), Decimal("18"),
                                        extra={"hsn": "84713010"})]))
    assert any(p["key"] == "unit" for p in exc.value.problems)


def test_schema_check_is_real():
    p = _p(_doc())
    p["ItemList"][0]["GstRt"] = 16
    assert FMT.schema_errors(json.dumps(p))
    p = _p(_doc())
    p["SellerDtls"]["Stat"] = "KA"    # unknown key rejected (strict)
    assert FMT.schema_errors(json.dumps(p))


def test_engine_marks_b2c_not_applicable(db):
    import uuid

    from platform.einvoicing.engine import clear_national

    res = clear_national(tenant_id=uuid.uuid4(), scope="default", mode="in_gst", doc=_doc(buyer=_buyer(gstin="")))
    assert res.status == "not_applicable"


def test_unconfigured_gsp_refuses(monkeypatch):
    monkeypatch.delenv("IN_GSP_BASE_URL", raising=False)
    with pytest.raises(TransportNotConfigured):
        FMT.submit("{}", _doc())
