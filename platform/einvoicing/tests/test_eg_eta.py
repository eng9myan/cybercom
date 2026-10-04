"""
ETA e-invoice (Egypt, Invoice v1.0) builder tests. Every payload is
validated against the authored JSON Schema under schemas/eg/ (see that
file's $comment for why it's authored, not vendored).
"""
import json
from datetime import datetime
from decimal import Decimal

import pytest

from platform.einvoicing.national import EInvoiceDataMissing, TransportNotConfigured
from platform.einvoicing.national.base import DocInput, LineInput, PartyInput
from platform.einvoicing.national.eg_eta import EgEta, canonical_serialize

FMT = EgEta()

SELLER_TRN = "123456789"
BUYER_TRN = "987654321"


def _seller(tax_id=SELLER_TRN, **extra):
    return PartyInput(tax_id=tax_id, name="Cycom Egypt LLC", street="17 Nabil Al Wakad", city="Dokki",
                      postal_code="12311", country_code="EG", region="Giza",
                      extra={"activity_code": "9478", "default_item_type": "EGS", **extra})


def _buyer(tax_id=BUYER_TRN, **kw):
    base = dict(tax_id=tax_id, name="Buyer Co", street="10 Tahrir St", city="Cairo",
                postal_code="11511", country_code="EG", region="Cairo")
    base.update(kw)
    return PartyInput(**base)


def _doc(**kw):
    base = dict(number="INV-2026-0001", issue_dt=datetime(2026, 9, 1, 13, 15, 0), currency="EGP",
                seller=_seller(), buyer=_buyer(),
                lines=[LineInput("Office chairs", Decimal("4"), Decimal("500.00"), Decimal("14"),
                                 extra={"item_code": "10003752", "unit_type": "PCE"})])
    base.update(kw)
    return DocInput(**base)


def _p(doc):
    return json.loads(FMT.build(doc))["document"]


def test_standard_rate_line_and_schema_valid():
    doc = _doc()
    built = FMT.build(doc)
    assert FMT.schema_errors(built) == []
    p = json.loads(built)["document"]
    assert p["documentType"] == "i"
    assert p["issuer"]["id"] == SELLER_TRN
    assert p["issuer"]["type"] == "B"
    assert p["receiver"]["id"] == BUYER_TRN
    line = p["invoiceLines"][0]
    assert line["salesTotal"] == 2000.0
    assert line["taxableItems"][0] == {"taxType": "T1", "amount": 280.0, "subType": "V009", "rate": 14.0}
    assert p["netAmount"] == 2000.0
    assert p["taxTotals"] == [{"taxType": "T1", "amount": 280.0}]
    assert p["totalAmount"] == 2280.0


def test_zero_rated_line_defaults_to_exempt_subtype():
    p = _p(_doc(lines=[LineInput("Export-exempt item", Decimal("1"), Decimal("100"), Decimal("0"),
                                 extra={"item_code": "X1", "unit_type": "PCE"})]))
    assert p["invoiceLines"][0]["taxableItems"][0]["subType"] == "V003"


def test_explicit_tax_subtype_overrides_the_default():
    p = _p(_doc(lines=[LineInput("Export item", Decimal("1"), Decimal("100"), Decimal("0"),
                                 extra={"item_code": "X1", "unit_type": "PCE", "tax_subtype": "V001"})]))
    assert p["invoiceLines"][0]["taxableItems"][0]["subType"] == "V001"


def test_non_egypt_buyer_is_not_applicable():
    doc = _doc(buyer=_buyer(country_code="US", tax_id=""))
    assert FMT.not_applicable_reason(doc)


def test_anonymous_b2c_receiver_gets_placeholder_id():
    p = _p(_doc(buyer=_buyer(tax_id="")))
    assert p["receiver"] == {"type": "P", "id": "0", "name": "Buyer Co",
                             "address": p["receiver"]["address"]}


def test_invalid_trn_and_rate_refused():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(seller=_seller(tax_id="123"),
                       lines=[LineInput("x", Decimal("1"), Decimal("1"), Decimal("16"),
                                        extra={"item_code": "X", "unit_type": "PCE"})]))
    keys = {(p["scope"], p["key"]) for p in exc.value.problems}
    assert ("seller", "tax_id") in keys and ("line[1]", "tax_percent") in keys


def test_credit_note_needs_the_original():
    with pytest.raises(EInvoiceDataMissing):
        FMT.build(_doc(is_credit_note=True))
    p = _p(_doc(is_credit_note=True, number="CN-2026-0001", original_number="XYZABCDEFGHIJKLMNOPQRSTUVW"))
    assert p["documentType"] == "c"
    assert p["references"] == [{"uuid": "XYZABCDEFGHIJKLMNOPQRSTUVW"}]


def test_foreign_currency_needs_an_exchange_rate():
    with pytest.raises(EInvoiceDataMissing) as exc:
        FMT.build(_doc(currency="USD"))
    assert any(p["key"] == "currency_exchange_rate" for p in exc.value.problems)
    p = _p(_doc(currency="USD", extra={"currency_exchange_rate": "48.5"}))
    assert p["invoiceLines"][0]["unitValue"]["currencyExchangeRate"] == 48.5
    assert p["invoiceLines"][0]["unitValue"]["amountEGP"] == 24250.0


def test_schema_check_is_real():
    p = _p(_doc())
    p["invoiceLines"][0]["taxableItems"][0]["taxType"] = "T99"
    assert FMT.schema_errors(json.dumps({"document": p}))


def test_canonical_serialize_uppercases_names_and_repeats_array_names():
    doc_dict = {"internalId": "AZ-1", "taxTotals": [{"taxType": "T1", "amount": 1.0}]}
    out = canonical_serialize(doc_dict)
    assert out.startswith('"INTERNALID""AZ-1"')
    assert '"TAXTOTALS""TAXTOTALS"' in out
    assert '"TAXTYPE""T1"' in out


def test_unsigned_without_certificate_refuses():
    assert FMT.signing_status() is False
    with pytest.raises(TransportNotConfigured):
        FMT.sign(FMT.build(_doc()), _doc())


def test_unconfigured_transport_refuses():
    with pytest.raises(TransportNotConfigured):
        FMT.submit("{}", _doc())
