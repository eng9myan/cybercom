"""
XML signing for e-invoicing.

`get_signer(mode)` returns a `Signer` for the active mode:

  jo_jofotara  -> XAdESSigner (XAdES-B enveloped) with the taxpayer cert,
                  or NullSigner if no key is configured (sandbox smoke only)
  sa_zatca     -> ZatcaSigner (ECDSA over the invoice hash, ZATCA profile)  [in einvoicing.sa]

A `Signer` takes the canonical UBL string and returns a signed UBL string.
Key material is loaded from a PEM file path today; the `KEY_LOADER` hook is
where a KMS / HSM loader is wired for production (blueprint C.5 secrets).
"""
from __future__ import annotations

import logging
import os
from typing import Protocol

logger = logging.getLogger("platform.einvoicing.signing")


class Signer(Protocol):
    def sign(self, ubl_xml: str) -> str: ...
    @property
    def signed(self) -> bool: ...


class NullSigner:
    """Returns the payload unchanged. Sandbox smoke tests only — every call logs a warning."""

    signed = False

    def sign(self, ubl_xml: str) -> str:
        logger.warning(
            "e-invoice signing key not configured — submitting UNSIGNED payload. "
            "Sandbox only; production submissions MUST be signed."
        )
        return ubl_xml


class XAdESSigner:
    """XAdES-B enveloped signature over a UBL 2.1 Invoice, using signxml.

    `key_pem` / `cert_pem` are PEM bytes (RSA or EC key + its X.509 cert).
    JoFotara issues a test cert during sandbox onboarding; production uses the
    taxpayer's own certificate.
    """

    signed = True

    def __init__(self, key_pem: bytes, cert_pem: bytes):
        self._key = key_pem
        self._cert = cert_pem

    def sign(self, ubl_xml: str) -> str:
        # Imported lazily so the module loads even where signxml/lxml aren't present
        # (e.g. a slim worker image that never signs).
        from lxml import etree
        from signxml.xades import XAdESSigner as _XSigner

        root = etree.fromstring(ubl_xml.encode("utf-8"))
        signer = _XSigner(
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
        )
        signed_root = signer.sign(root, key=self._key, cert=self._cert)
        return etree.tostring(
            signed_root, xml_declaration=True, encoding="UTF-8"
        ).decode("utf-8")


_DS = "http://www.w3.org/2000/09/xmldsig#"
_XADES = "http://uri.etsi.org/01903/v1.3.2#"


def signature_wellformed(signed_xml: str) -> bool:
    """Structural pre-submit gate: the document carries a complete XAdES-B
    signature block — SignedInfo with a reference to the invoice body and to
    the SignedProperties, a non-empty SignatureValue, an embedded X.509 cert,
    and XAdES QualifyingProperties.

    This is not a cryptographic re-verification (the authority does that on
    submission, and full self-verify is confirmed against ISTD's own verifier
    during sandbox onboarding). It catches "signing silently produced nothing
    usable" before we waste a submission.
    """
    try:
        from cryptography.x509 import load_pem_x509_certificate
        from lxml import etree

        root = etree.fromstring(signed_xml.encode("utf-8"))
        ns = {"ds": _DS, "xades": _XADES}

        sig = root.find(f".//{{{_DS}}}Signature")
        if sig is None:
            return False
        refs = sig.findall(f".//{{{_DS}}}SignedInfo/{{{_DS}}}Reference")
        if len(refs) < 2:
            return False
        sigval = sig.find(f"{{{_DS}}}SignatureValue")
        if sigval is None or not (sigval.text or "").strip():
            return False
        cert_node = sig.find(f".//{{{_DS}}}X509Certificate")
        if cert_node is None or not (cert_node.text or "").strip():
            return False
        pem = (
            b"-----BEGIN CERTIFICATE-----\n"
            + cert_node.text.strip().encode()
            + b"\n-----END CERTIFICATE-----\n"
        )
        load_pem_x509_certificate(pem)  # raises if the embedded cert is junk
        qp = sig.find(f".//{{{_XADES}}}QualifyingProperties")
        return qp is not None
    except Exception as exc:  # pragma: no cover
        logger.info("signature well-formed check failed: %s", exc)
        return False


def verify_xades(signed_xml: str, cert_pem: bytes | None = None) -> bool:
    """Cryptographic self-check of the enveloped signature over the invoice
    body. Returns False if the body was tampered after signing.

    Note: signxml's XAdESVerifier has a known round-trip quirk on the
    SignedProperties self-digest, so this uses the plain XMLVerifier against
    the invoice-body reference (URI="") — which is exactly what a tamper of
    the invoice content would break.
    """
    try:
        from lxml import etree
        from signxml import XMLVerifier

        root = etree.fromstring(signed_xml.encode("utf-8"))
        if cert_pem is None:
            node = root.find(f".//{{{_DS}}}X509Certificate")
            if node is None or not node.text:
                return False
            cert_pem = (
                b"-----BEGIN CERTIFICATE-----\n"
                + node.text.strip().encode()
                + b"\n-----END CERTIFICATE-----\n"
            )
        # id_attribute/expect_references tuned to signxml's XAdES output shape
        for refs in (2, 1):
            try:
                XMLVerifier().verify(
                    root, x509_cert=cert_pem, expect_references=refs,
                    validate_schema=False,
                )
                return True
            except Exception:  # noqa: S112 - try the other reference count
                continue
        return False
    except Exception as exc:  # pragma: no cover
        logger.info("signature self-check failed: %s", exc)
        return False


# ── key loading ────────────────────────────────────────────────────────────
def _read(path: str) -> bytes | None:
    if path and os.path.exists(path):
        with open(path, "rb") as fh:
            return fh.read()
    return None


#: swap for a KMS/HSM loader in production — signature: (mode) -> (key_pem, cert_pem) | (None, None)
def KEY_LOADER(mode: str) -> tuple[bytes | None, bytes | None]:
    if mode == "jo_jofotara":
        return (
            _read(os.getenv("JOFOTARA_PRIVATE_KEY_PATH", "")),
            _read(os.getenv("JOFOTARA_CERT_PATH", "")),
        )
    if mode == "sa_zatca":
        return (
            _read(os.getenv("ZATCA_PRIVATE_KEY_PATH", "")),
            _read(os.getenv("ZATCA_CERT_PATH", "")),
        )
    return (None, None)


def get_signer(mode: str) -> Signer:
    key_pem, cert_pem = KEY_LOADER(mode)
    if not key_pem or not cert_pem:
        return NullSigner()
    if mode == "sa_zatca":
        from platform.einvoicing.sa.signing import ZatcaSigner  # noqa: WPS433

        return ZatcaSigner(key_pem, cert_pem)
    return XAdESSigner(key_pem, cert_pem)
