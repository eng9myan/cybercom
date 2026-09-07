"""
XAdES-B enveloped signing for UBL 2.1 e-invoices (ZATCA / JoFotara shape).

Status: this produces a *structurally complete* XAdES-B signature — canonical
digest of the invoice, an RSA/ECDSA signature over a real ``ds:SignedInfo``,
and the ``xades:QualifyingProperties`` block (signing time + signing-cert
digest) that both schemes require, all wrapped in ``ext:UBLExtensions``.

It has **not** been run through the ZATCA SDK / Fatoora conformance validator
or the JoFotara test bench. Do that — and confirm the required canonicalization
transforms and the secp256k1 curve with the onboarded CSID — before switching
live clearance on. Until then ``services.submit`` still routes unsigned docs to
the operator portal rather than faking a cleared response.

Credentials live on ``TaxProfile.certificate_pem`` / ``private_key_pem`` and are
supplied by the founder after the seller is onboarded; nothing here generates
or stores keys.
"""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


class SigningNotConfigured(RuntimeError):
    """Raised when a TaxProfile has no usable cert / private-key pair."""


_DS = "http://www.w3.org/2000/09/xmldsig#"
_XADES = "http://uri.etsi.org/01903/v1.3.2#"
_C14N = "http://www.w3.org/2006/12/xml-c14n11"
_ENV = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"
_SHA256 = "http://www.w3.org/2001/04/xmlenc#sha256"
_SIG_RSA = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
_SIG_ECDSA = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256"


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _canonical(xml: str) -> bytes:
    """C14N 1.1 of the invoice document (stdlib, no lxml)."""
    return ET.canonicalize(xml_data=xml, strip_text=False).encode("utf-8")


def invoice_digest(ubl_xml: str) -> str:
    """Base64 SHA-256 of the canonical invoice — the scheme 'invoice hash'."""
    return _b64(hashlib.sha256(_canonical(ubl_xml)).digest())


# --------------------------------------------------------------------------- keys

def load_credentials(profile) -> tuple[object, x509.Certificate]:
    cert_pem = (getattr(profile, "certificate_pem", "") or "").strip()
    key_pem = (getattr(profile, "private_key_pem", "") or "").strip()
    if not cert_pem or not key_pem:
        raise SigningNotConfigured(
            "TaxProfile is missing certificate_pem / private_key_pem — the "
            "seller's CSID has not been installed.")
    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"))
        key = serialization.load_pem_private_key(key_pem.encode("utf-8"), password=None)
    except ValueError as exc:  # malformed PEM
        raise SigningNotConfigured(f"Could not parse CSID material: {exc}") from exc
    return key, cert


def _sign_bytes(key, data: bytes) -> tuple[str, bytes]:
    if isinstance(key, rsa.RSAPrivateKey):
        return _SIG_RSA, key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    if isinstance(key, ec.EllipticCurvePrivateKey):
        return _SIG_ECDSA, key.sign(data, ec.ECDSA(hashes.SHA256()))
    raise SigningNotConfigured(f"Unsupported key type {type(key).__name__}")


# ------------------------------------------------------------------- XAdES build

def _signed_props_xml(cert: x509.Certificate, signing_time: datetime) -> str:
    cert_digest = _b64(cert.fingerprint(hashes.SHA256()))
    issuer = cert.issuer.rfc4514_string()
    serial = cert.serial_number
    return (
        '<xades:SignedProperties'
        f' xmlns:xades="{_XADES}" xmlns:ds="{_DS}" Id="xadesSignedProperties">'
        "<xades:SignedSignatureProperties>"
        f"<xades:SigningTime>{signing_time.isoformat()}</xades:SigningTime>"
        "<xades:SigningCertificate><xades:Cert>"
        "<xades:CertDigest>"
        f'<ds:DigestMethod Algorithm="{_SHA256}"/>'
        f"<ds:DigestValue>{cert_digest}</ds:DigestValue>"
        "</xades:CertDigest>"
        "<xades:IssuerSerial>"
        f"<ds:X509IssuerName>{issuer}</ds:X509IssuerName>"
        f"<ds:X509SerialNumber>{serial}</ds:X509SerialNumber>"
        "</xades:IssuerSerial>"
        "</xades:Cert></xades:SigningCertificate>"
        "</xades:SignedSignatureProperties>"
        "</xades:SignedProperties>"
    )


def _digest(text: str) -> str:
    return _b64(hashlib.sha256(ET.canonicalize(xml_data=text).encode("utf-8")).digest())


def sign(ubl_xml: str, profile, *, signing_time: datetime | None = None) -> dict:
    """Return {'signed_xml', 'invoice_hash', 'signature', 'signing_time'}.

    Raises SigningNotConfigured if the profile has no CSID material.
    """
    key, cert = load_credentials(profile)
    signing_time = (signing_time or datetime.now(timezone.utc)).replace(microsecond=0)

    inv_digest = invoice_digest(ubl_xml)
    signed_props = _signed_props_xml(cert, signing_time)
    props_digest = _digest(signed_props)

    signed_info = (
        f'<ds:SignedInfo xmlns:ds="{_DS}">'
        f'<ds:CanonicalizationMethod Algorithm="{_C14N}"/>'
        f'<ds:SignatureMethod Algorithm="{_SIG_ECDSA if isinstance(key, ec.EllipticCurvePrivateKey) else _SIG_RSA}"/>'
        '<ds:Reference Id="invoiceSignedData" URI="">'
        f'<ds:Transforms><ds:Transform Algorithm="{_ENV}"/>'
        f'<ds:Transform Algorithm="{_C14N}"/></ds:Transforms>'
        f'<ds:DigestMethod Algorithm="{_SHA256}"/>'
        f"<ds:DigestValue>{inv_digest}</ds:DigestValue></ds:Reference>"
        '<ds:Reference Type="http://uri.etsi.org/01903#SignedProperties" URI="#xadesSignedProperties">'
        f'<ds:DigestMethod Algorithm="{_SHA256}"/>'
        f"<ds:DigestValue>{props_digest}</ds:DigestValue></ds:Reference>"
        "</ds:SignedInfo>"
    )
    alg, raw_sig = _sign_bytes(key, ET.canonicalize(xml_data=signed_info).encode("utf-8"))
    sig_value = _b64(raw_sig)
    cert_b64 = _b64(cert.public_bytes(serialization.Encoding.DER))

    signature = (
        f'<ds:Signature xmlns:ds="{_DS}" Id="signature">'
        f"{signed_info}"
        f"<ds:SignatureValue>{sig_value}</ds:SignatureValue>"
        f"<ds:KeyInfo><ds:X509Data><ds:X509Certificate>{cert_b64}</ds:X509Certificate>"
        "</ds:X509Data></ds:KeyInfo>"
        f'<ds:Object><xades:QualifyingProperties xmlns:xades="{_XADES}" Target="#signature">'
        f"{signed_props}</xades:QualifyingProperties></ds:Object>"
        "</ds:Signature>"
    )

    ubl_ext = (
        "<ext:UBLExtensions "
        'xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">'
        "<ext:UBLExtension><ext:ExtensionContent>"
        f"{signature}"
        "</ext:ExtensionContent></ext:UBLExtension></ext:UBLExtensions>"
    )
    # inject the extensions block as the first child of <Invoice>
    marker = ">"
    idx = ubl_xml.index("<Invoice")
    close = ubl_xml.index(marker, idx) + 1
    signed_xml = ubl_xml[:close] + "\n  " + ubl_ext + ubl_xml[close:]

    return {
        "signed_xml": signed_xml,
        "invoice_hash": inv_digest,
        "signature": sig_value,
        "signing_time": signing_time,
    }


def sign_document(doc) -> object:
    """Sign an EInvoiceDocument in place. No-op-with-warning if not configured."""
    from . import services

    if not doc.ubl_xml:
        services.generate(doc.invoice)
        doc.refresh_from_db()
    profile = getattr(doc.invoice.company, "tax_profile", None)
    if profile is None:
        raise SigningNotConfigured("Company has no tax profile.")
    try:
        result = sign(doc.ubl_xml, profile, signing_time=None)
    except SigningNotConfigured as exc:
        doc.warnings = (doc.warnings or []) + [f"Not signed: {exc}"]
        doc.save(update_fields=["warnings", "updated_at", "version"])
        return doc
    doc.signed_xml = result["signed_xml"]
    doc.invoice_hash = result["invoice_hash"]
    doc.status = "signed"
    doc.save(update_fields=["signed_xml", "invoice_hash", "status", "updated_at", "version"])
    return doc
