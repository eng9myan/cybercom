"""ZATCA (KSA) — UBL builder, TLV QR, ECDSA stamp, engine sa_zatca path."""
import base64
import datetime
from decimal import Decimal

import pytest

from platform.einvoicing.engine import SellerProfile, clear_invoice
from platform.einvoicing.hashing import GENESIS_PIH
from platform.einvoicing.models import EInvoiceSequence
from platform.einvoicing.sa.qr import decode_qr, encode_qr
from platform.einvoicing.sa.signing import ZatcaSigner, canonical_hash, verify_hash_signature
from platform.einvoicing.sa.ubl import SaInvoiceData, build_sa_ubl
from platform.einvoicing.ubl import UblLine, UblParty

T = "11111111-1111-1111-1111-111111111111"


def _sa_data(**over):
    d = dict(
        number="INV-1", uuid="4c8e0000-0000-0000-0000-000000000001",
        issue_dt=datetime.datetime(2026, 7, 5, 12, 0), currency="SAR",
        icv=1, pih=GENESIS_PIH,
        seller=UblParty(tin="311111111100003", name="Riyadh Retail", country_code="SA"),
        seller_vat="311111111100003",
        buyer=UblParty(tin="", name="", country_code="SA"), buyer_vat="",
        lines=[
            UblLine(line_id="1", name="Widget", quantity=Decimal("2"),
                    unit_price=Decimal("50.00"), tax_percent=Decimal("15")),
        ],
    )
    d.update(over)
    return SaInvoiceData(**d)


# ── UBL ────────────────────────────────────────────────────────────────────
def test_sa_ubl_totals_and_structure():
    d = _sa_data()
    assert d.line_extension_total == Decimal("100.00")
    assert d.tax_total == Decimal("15.00")          # 15% KSA VAT
    assert d.tax_inclusive_total == Decimal("115.00")

    xml = build_sa_ubl(d)
    assert "<cbc:ProfileID>reporting:1.0</cbc:ProfileID>" in xml
    assert 'currencyID="SAR">115.000</cbc:PayableAmount>' in xml
    assert "<cbc:TaxCurrencyCode>SAR</cbc:TaxCurrencyCode>" in xml
    assert '<cbc:ID schemeID="CRN">311111111100003</cbc:ID>' in xml
    assert "0200000" not in xml                      # default standard subtype
    assert 'name="0100000"' in xml


def test_sa_ubl_simplified_subtype():
    xml = build_sa_ubl(_sa_data(is_simplified=True))
    assert 'name="0200000"' in xml


# ── QR (TLV) ───────────────────────────────────────────────────────────────
def test_qr_tlv_roundtrips_tags_1_to_5():
    b64 = encode_qr(
        seller_name="Riyadh Retail", seller_vat="311111111100003",
        timestamp_iso="2026-07-05T12:00:00", invoice_total="115.00", vat_total="15.00",
    )
    tags = decode_qr(b64)
    assert tags[1] == b"Riyadh Retail"
    assert tags[2] == b"311111111100003"
    assert tags[3] == b"2026-07-05T12:00:00"
    assert tags[4] == b"115.00"
    assert tags[5] == b"15.00"
    assert 6 not in tags                             # no hash/sig supplied


def test_qr_includes_hash_and_signature_when_supplied():
    fake_hash = base64.b64encode(b"x" * 32).decode()
    fake_sig = base64.b64encode(b"y" * 64).decode()
    b64 = encode_qr(
        seller_name="S", seller_vat="V", timestamp_iso="t",
        invoice_total="1", vat_total="0",
        xml_hash_b64=fake_hash, signature_b64=fake_sig,
    )
    tags = decode_qr(b64)
    assert base64.b64encode(tags[6]).decode() == fake_hash
    assert base64.b64encode(tags[7]).decode() == fake_sig


# ── ECDSA stamp ────────────────────────────────────────────────────────────
def _ec_csid():
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography import x509
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256K1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ZATCA CSID Test")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    kp = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                           serialization.NoEncryption())
    cp = cert.public_bytes(serialization.Encoding.PEM)
    return kp, cp


def test_zatca_stamp_signs_and_verifies():
    kp, cp = _ec_csid()
    xml = build_sa_ubl(_sa_data())
    parts = ZatcaSigner(kp, cp).sign_hash(xml)

    assert parts["invoice_hash"] == canonical_hash(xml)
    assert verify_hash_signature(xml, parts["signature"], parts["public_key"]) is True
    # a tampered doc no longer matches
    assert verify_hash_signature(xml.replace("Widget", "Gadget"),
                                 parts["signature"], parts["public_key"]) is False


# ── engine ────────────────────────────────────────────────────────────────
class _FakeZatca:
    def __init__(self, *, simplified_ok=True, standard_ok=True):
        self.simplified_ok = simplified_ok
        self.standard_ok = standard_ok
        self.calls = []

    def submit(self, *, is_simplified, invoice_hash_b64, uuid, invoice_b64):
        self.calls.append(("simplified" if is_simplified else "standard", uuid))
        if is_simplified:
            return {"status": "reported" if self.simplified_ok else "INVALID",
                    "reference": "REPORTED", "qr": "", "raw": {}}
        return {"status": "cleared" if self.standard_ok else "INVALID",
                "reference": "CLEARED", "qr": "ZATCA_QR==", "raw": {}}


@pytest.mark.django_db
def test_engine_sa_standard_clearance_advances_sequence():
    fz = _FakeZatca()
    args = dict(
        tenant_id=T, scope="default", country_code="SA", currency="SAR",
        issue_dt=datetime.datetime(2026, 7, 5, 12, 0),
        seller=SellerProfile(tin="311111111100003", name="Riyadh Retail", city="Riyadh"),
        buyer_tin="399999999900003", buyer_name="Buyer Co", buyer_city="Jeddah",
        lines=[{"name": "Widget", "quantity": 2, "unit_price": "50.00", "tax_percent": 15}],
        client=fz,
    )
    r1 = clear_invoice(number="INV-1", **args)
    r2 = clear_invoice(number="INV-2", **args)
    assert r1.status == "cleared" and r1.mode == "sa_zatca" and r1.icv == 1
    assert r2.icv == 2 and r2.pih == r1.invoice_hash
    assert r1.qr == "ZATCA_QR=="
    seq = EInvoiceSequence.objects.get(tenant_id=T, scope="default", mode="sa_zatca")
    assert seq.next_icv == 3
    assert [c[0] for c in fz.calls] == ["standard", "standard"]


@pytest.mark.django_db
def test_engine_sa_simplified_uses_our_own_qr():
    fz = _FakeZatca()
    r = clear_invoice(
        tenant_id=T, scope="default", country_code="SA", currency="SAR", number="INV-B2C",
        issue_dt=datetime.datetime(2026, 7, 5, 12, 0),
        seller=SellerProfile(tin="311111111100003", name="Riyadh Retail"),
        buyer_tin="", buyer_name="", buyer_city="",
        lines=[{"name": "Coffee", "quantity": 1, "unit_price": "12.00", "tax_percent": 15}],
        is_simplified=True, client=fz,
    )
    assert r.status == "reported"
    tags = decode_qr(r.qr)                            # engine embedded a TLV QR
    assert tags[1] == b"Riyadh Retail"
    assert tags[4] == b"13.80"                        # 12 + 15%


@pytest.mark.django_db
def test_engine_sa_rejection_keeps_icv():
    fz = _FakeZatca(standard_ok=False)
    r = clear_invoice(
        tenant_id=T, scope="default", country_code="SA", currency="SAR", number="INV-BAD",
        issue_dt=datetime.datetime(2026, 7, 5, 12, 0),
        seller=SellerProfile(tin="311111111100003", name="Riyadh Retail"),
        buyer_tin="399999999900003", buyer_name="Buyer", buyer_city="",
        lines=[{"name": "Widget", "quantity": 1, "unit_price": "50", "tax_percent": 15}],
        client=fz,
    )
    assert r.status == "INVALID" and not r.ok
    seq = EInvoiceSequence.objects.get(tenant_id=T, scope="default", mode="sa_zatca")
    assert seq.next_icv == 1
