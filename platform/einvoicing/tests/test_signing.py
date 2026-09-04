"""XAdES signing tests — real signature over a real UBL document."""
import datetime
from decimal import Decimal

import pytest

from platform.einvoicing.signing import (
    NullSigner,
    XAdESSigner,
    get_signer,
    signature_wellformed,
    verify_xades,
)
from platform.einvoicing.ubl import JoInvoiceData, UblLine, UblParty, build_jo_ubl


def _self_signed():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Cafe Amman Test")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=True, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    return key_pem, cert_pem


def _ubl():
    return build_jo_ubl(JoInvoiceData(
        number="INV-9", uuid="4c8e0000-0000-0000-0000-000000000009",
        issue_dt=datetime.datetime(2026, 7, 5, 12, 0), currency="JOD", icv=1,
        pih="0" * 64,
        seller=UblParty(tin="200123456", name="Cafe Amman"),
        buyer=UblParty(tin="", name="General Public"),
        lines=[UblLine(line_id="1", name="Latte", quantity=Decimal("1"),
                       unit_price=Decimal("2.500"), tax_percent=Decimal("16"))],
    ))


def test_null_signer_returns_payload_unchanged():
    xml = _ubl()
    assert NullSigner().sign(xml) == xml
    assert NullSigner().signed is False


def test_get_signer_falls_back_to_null_without_key(monkeypatch):
    monkeypatch.delenv("JOFOTARA_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("JOFOTARA_CERT_PATH", raising=False)
    assert isinstance(get_signer("jo_jofotara"), NullSigner)


def test_xades_signature_is_produced_and_wellformed():
    key_pem, cert_pem = _self_signed()
    signed = XAdESSigner(key_pem, cert_pem).sign(_ubl())

    assert "Signature" in signed
    assert "http://uri.etsi.org/01903" in signed          # XAdES namespace
    assert "<xades:SignedProperties" in signed
    assert signature_wellformed(signed) is True


def test_tampered_signed_doc_fails_verification():
    key_pem, cert_pem = _self_signed()
    signed = XAdESSigner(key_pem, cert_pem).sign(_ubl())
    tampered = signed.replace("Latte", "Mocha")
    # the invoice-body digest no longer matches -> crypto self-check fails
    assert verify_xades(tampered) is False


def test_missing_signature_is_not_wellformed():
    assert signature_wellformed(_ubl()) is False


@pytest.mark.django_db
def test_engine_signs_when_a_key_is_configured(tmp_path, monkeypatch):
    from platform.einvoicing.engine import SellerProfile, clear_invoice

    key_pem, cert_pem = _self_signed()
    kp, cp = tmp_path / "k.pem", tmp_path / "c.pem"
    kp.write_bytes(key_pem)
    cp.write_bytes(cert_pem)
    monkeypatch.setenv("JOFOTARA_PRIVATE_KEY_PATH", str(kp))
    monkeypatch.setenv("JOFOTARA_CERT_PATH", str(cp))

    captured = {}

    class _Client:
        def submit_invoice(self, xml, uuid):
            captured["xml"] = xml
            return {"status": "submitted", "reference": "JO-1", "qr": "", "raw": {}}

    r = clear_invoice(
        tenant_id="11111111-1111-1111-1111-111111111111", scope="default",
        country_code="JO", currency="JOD", number="INV-SIGNED",
        issue_dt=datetime.datetime(2026, 7, 5, 12, 0),
        seller=SellerProfile(tin="200123456", name="Cafe Amman"),
        buyer_tin="", buyer_name="General Public", buyer_city="Amman",
        lines=[{"name": "Latte", "quantity": 1, "unit_price": "2.500", "tax_percent": 16}],
        client=_Client(),
    )
    assert r.status == "cleared"
    assert "http://uri.etsi.org/01903" in captured["xml"]   # the submitted doc is signed
