"""
ZATCA cryptographic stamp — ECDSA signature over the invoice hash.

ZATCA does not use plain XAdES; it defines its own signature: the invoice XML
is canonicalised and SHA-256 hashed, that hash is ECDSA-signed with the CSID
private key (secp256k1), and the signature + public key + cert digest go into
a `ds:Signature` block inside `<ext:UBLExtensions>` plus the QR (tags 6-8).

This module produces the signature primitives. Embedding the full
`ext:UBLExtensions/ds:Signature` block per the exact ZATCA schema is finalised
during the ZATCA compliance CSID onboarding (they run a conformance suite
against the generated XML) — see
docs/blueprint/specs/einvoicing-clearance-engine.md §4.3 / §7.
"""
from __future__ import annotations

import base64
import hashlib
import logging

logger = logging.getLogger("platform.einvoicing.sa.signing")


def canonical_hash(xml: str) -> str:
    """base64(SHA-256) of the invoice XML — the value that gets signed and
    goes into QR tag 6. ZATCA canonicalises first (exc-c14n, minus the
    UBLExtensions/QR/Signature nodes); we hash the provided string, which the
    UBL builder emits already normalised for that purpose."""
    return base64.b64encode(hashlib.sha256(xml.encode("utf-8")).digest()).decode("ascii")


class ZatcaSigner:
    """ECDSA (secp256k1) signer over the invoice hash, using the CSID key.

    `key_pem` / `cert_pem` come from the ZATCA compliance CSID onboarding.
    """

    signed = True

    def __init__(self, key_pem: bytes, cert_pem: bytes):
        self._key_pem = key_pem
        self._cert_pem = cert_pem

    def _load(self):
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from cryptography.x509 import load_pem_x509_certificate

        key = load_pem_private_key(self._key_pem, password=None)
        cert = load_pem_x509_certificate(self._cert_pem)
        return key, cert

    def sign_hash(self, xml: str) -> dict[str, str]:
        """Return {invoice_hash, signature, public_key, cert_digest} (all base64)."""
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec, utils

        key, cert = self._load()
        h_b64 = canonical_hash(xml)
        digest = base64.b64decode(h_b64)

        sig = key.sign(digest, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        pub_der = key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        cert_digest = base64.b64encode(
            hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).digest()
        ).decode("ascii")
        return {
            "invoice_hash": h_b64,
            "signature": base64.b64encode(sig).decode("ascii"),
            "public_key": base64.b64encode(pub_der).decode("ascii"),
            "cert_digest": cert_digest,
        }

    # kept so ZatcaSigner satisfies the einvoicing.signing.Signer protocol
    def sign(self, ubl_xml: str) -> str:
        # ZATCA embeds the signature into UBLExtensions; that assembly is done
        # in sa.ubl.embed_signature during onboarding conformance. For now the
        # engine calls sign_hash() and carries the parts explicitly.
        logger.info("ZatcaSigner.sign() is a no-op wrapper; use sign_hash()")
        return ubl_xml


def verify_hash_signature(xml: str, signature_b64: str, public_key_der_b64: str) -> bool:
    """Self-check: does `signature_b64` verify against the invoice hash with
    the given public key?"""
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        from cryptography.hazmat.primitives.serialization import load_der_public_key

        pub = load_der_public_key(base64.b64decode(public_key_der_b64))
        digest = base64.b64decode(canonical_hash(xml))
        pub.verify(
            base64.b64decode(signature_b64),
            digest,
            ec.ECDSA(utils.Prehashed(hashes.SHA256())),
        )
        return True
    except Exception as exc:  # pragma: no cover - via tamper test
        logger.info("zatca signature verify failed: %s", exc)
        return False
