"""
ZATCA QR — TLV (Tag-Length-Value) encoded, base64 wrapped.

Nine tags per the ZATCA spec:
  1 seller name            2 seller VAT number     3 invoice timestamp (ISO 8601)
  4 invoice total (incl VAT)  5 VAT total           6 XML invoice hash (base64)
  7 ECDSA signature (base64)   8 ECDSA public key (DER, base64)
  9 signature of the stamp's public key (base64)   [production CSID only]

Tags 1-5 are always present. 6-9 are added once the invoice is hashed/signed.
For a simplified (B2C) invoice all 9 are embedded in the QR; for a standard
(B2B) invoice the QR is issued by ZATCA on clearance.
"""
from __future__ import annotations

import base64


def _tlv(tag: int, value: bytes) -> bytes:
    if not (1 <= tag <= 255):
        raise ValueError("tag out of range")
    if len(value) > 255:
        # ZATCA fields never exceed 255 bytes; guard rather than silently truncate.
        raise ValueError(f"TLV value for tag {tag} exceeds 255 bytes ({len(value)})")
    return bytes([tag, len(value)]) + value


def encode_qr(
    *,
    seller_name: str,
    seller_vat: str,
    timestamp_iso: str,
    invoice_total: str,
    vat_total: str,
    xml_hash_b64: str = "",
    signature_b64: str = "",
    public_key_der_b64: str = "",
    stamp_signature_b64: str = "",
) -> str:
    """Return the base64 TLV QR payload."""
    parts = [
        _tlv(1, seller_name.encode("utf-8")),
        _tlv(2, seller_vat.encode("utf-8")),
        _tlv(3, timestamp_iso.encode("utf-8")),
        _tlv(4, str(invoice_total).encode("utf-8")),
        _tlv(5, str(vat_total).encode("utf-8")),
    ]
    if xml_hash_b64:
        parts.append(_tlv(6, base64.b64decode(xml_hash_b64)))
    if signature_b64:
        parts.append(_tlv(7, base64.b64decode(signature_b64)))
    if public_key_der_b64:
        parts.append(_tlv(8, base64.b64decode(public_key_der_b64)))
    if stamp_signature_b64:
        parts.append(_tlv(9, base64.b64decode(stamp_signature_b64)))
    return base64.b64encode(b"".join(parts)).decode("ascii")


def decode_qr(b64: str) -> dict[int, bytes]:
    """Parse a base64 TLV QR back into {tag: value}. For tests + verification."""
    raw = base64.b64decode(b64)
    out: dict[int, bytes] = {}
    i = 0
    while i + 2 <= len(raw):
        tag = raw[i]
        length = raw[i + 1]
        val = raw[i + 2 : i + 2 + length]
        if len(val) != length:
            raise ValueError("truncated TLV")
        out[tag] = val
        i += 2 + length
    return out
