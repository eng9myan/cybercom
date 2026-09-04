"""Tests for the JoFotara UBL builder, hash chain, and clearance engine."""
from datetime import datetime
from decimal import Decimal

import pytest

from platform.einvoicing.engine import SellerProfile, clear_invoice, mode_for_country
from platform.einvoicing.hashing import GENESIS_PIH, chain_ok, invoice_hash
from platform.einvoicing.models import EInvoiceInteraction, EInvoiceSequence
from platform.einvoicing.ubl import JoInvoiceData, UblLine, UblParty, build_jo_ubl

T = "11111111-1111-1111-1111-111111111111"


# ── UBL builder ────────────────────────────────────────────────────────────
def _data(pih=GENESIS_PIH, icv=1):
    return JoInvoiceData(
        number="INV-001", uuid="4c8e0000-0000-0000-0000-000000000001",
        issue_dt=datetime(2026, 7, 5, 12, 0), currency="JOD", icv=icv, pih=pih,
        seller=UblParty(tin="200123456", name="Cafe Amman"),
        buyer=UblParty(tin="", name="General Public"),
        lines=[
            UblLine(line_id="1", name="Latte", quantity=Decimal("3"),
                    unit_price=Decimal("2.500"), tax_percent=Decimal("16")),
            UblLine(line_id="2", name="Water", quantity=Decimal("2"),
                    unit_price=Decimal("1.000"), tax_percent=Decimal("0")),
        ],
    )


def test_ubl_totals_tie_to_lines():
    d = _data()
    # 3*2.5 = 7.5 ; 2*1 = 2 ; line extension total 9.5
    assert d.line_extension_total == Decimal("9.500")
    # tax only on line 1: 7.5 * 16% = 1.2
    assert d.tax_total == Decimal("1.200")
    assert d.tax_inclusive_total == Decimal("10.700")


def test_ubl_has_pint_jo_structure():
    xml = build_jo_ubl(_data(pih="abc123==", icv=7))
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" in xml
    assert "<cbc:InvoiceTypeCode" in xml and ">388<" in xml
    assert "<cbc:ID>ICV</cbc:ID>" in xml and "<cbc:UUID>7</cbc:UUID>" in xml
    assert "<cbc:ID>PIH</cbc:ID>" in xml and "abc123==" in xml
    assert xml.count("<cac:InvoiceLine>") == 2
    # document-level payable amount matches the derived total
    assert 'currencyID="JOD">10.700</cbc:PayableAmount>' in xml


def test_ubl_tax_subtotals_split_by_rate():
    xml = build_jo_ubl(_data())
    # one S (16%) subtotal and one Z (0%) subtotal
    assert xml.count("<cac:TaxSubtotal>") == 2
    assert "<cbc:ID>S</cbc:ID>" in xml
    assert "<cbc:ID>Z</cbc:ID>" in xml


# ── hash chain ─────────────────────────────────────────────────────────────
def test_hash_is_deterministic_and_chain_verifies():
    xml = build_jo_ubl(_data())
    h1 = invoice_hash(xml)
    assert h1 == invoice_hash(xml)                     # deterministic
    h2 = invoice_hash(build_jo_ubl(_data(pih=h1, icv=2)))
    assert chain_ok([(GENESIS_PIH, h1), (h1, h2)])
    assert not chain_ok([(GENESIS_PIH, h1), ("wrong", h2)])


# ── engine ────────────────────────────────────────────────────────────────
class _FakeClient:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = []

    def submit_invoice(self, xml, uuid):
        self.calls.append((xml, uuid))
        if self.fail:
            raise RuntimeError("sandbox 503")
        return {"status": "submitted", "reference": f"JO-{len(self.calls):04d}",
                "qr": "QRDATA==", "raw": {"ok": True}}


@pytest.mark.django_db
def test_engine_clears_and_advances_the_sequence():
    fc = _FakeClient()
    args = dict(
        tenant_id=T, scope="default", country_code="JO", currency="JOD",
        issue_dt=datetime(2026, 7, 5, 12, 0),
        seller=SellerProfile(tin="200123456", name="Cafe Amman"),
        buyer_tin="", buyer_name="General Public", buyer_city="Amman",
        lines=[{"name": "Latte", "quantity": 3, "unit_price": "2.500", "tax_percent": 16}],
    )
    r1 = clear_invoice(number="INV-1", client=fc, **args)
    r2 = clear_invoice(number="INV-2", client=fc, **args)

    assert r1.status == "cleared" and r1.icv == 1 and r1.pih == GENESIS_PIH
    assert r2.status == "cleared" and r2.icv == 2 and r2.pih == r1.invoice_hash
    seq = EInvoiceSequence.objects.get(tenant_id=T, scope="default", mode="jo_jofotara")
    assert seq.next_icv == 3 and seq.last_hash == r2.invoice_hash
    assert EInvoiceInteraction.objects.filter(status="cleared").count() == 2


@pytest.mark.django_db
def test_engine_failure_does_not_advance_sequence():
    fc = _FakeClient(fail=True)
    r = clear_invoice(
        tenant_id=T, scope="default", country_code="JO", currency="JOD", number="INV-X",
        issue_dt=datetime(2026, 7, 5, 12, 0),
        seller=SellerProfile(tin="200123456", name="Cafe Amman"),
        buyer_tin="", buyer_name="General Public", buyer_city="Amman",
        lines=[{"name": "Latte", "quantity": 1, "unit_price": "2.500", "tax_percent": 16}],
        client=fc,
    )
    assert r.status == "rejected" and "503" in r.error
    seq = EInvoiceSequence.objects.get(tenant_id=T, scope="default", mode="jo_jofotara")
    assert seq.next_icv == 1                       # not advanced
    assert EInvoiceInteraction.objects.filter(status="rejected").count() == 1


def test_unimplemented_modes_raise():
    assert mode_for_country("SA") == "sa_zatca"
    with pytest.raises(NotImplementedError):
        clear_invoice(
            tenant_id=T, scope="default", country_code="SA", currency="SAR", number="INV-SA",
            issue_dt=datetime(2026, 7, 5, 12, 0),
            seller=SellerProfile(tin="1", name="X"), buyer_tin="", buyer_name="Y", buyer_city="",
            lines=[{"name": "Z", "quantity": 1, "unit_price": "1", "tax_percent": 15}],
        )
