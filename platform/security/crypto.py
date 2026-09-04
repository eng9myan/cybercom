"""
Per-tenant field encryption (canonical-data-model-v1.md §2.3).

A tenant's data-encryption key (DEK) is derived from a master key via
HKDF-SHA256 salted with the tenant id, so:
  * every tenant's ciphertext is under a distinct key,
  * there is no per-tenant DEK to store or wrap (rotation = rotate the master
    and re-encrypt), and
  * a leak of one tenant's derived key tells you nothing about another's.

Cipher: AES-256-GCM (authenticated) with a random 96-bit nonce per value.
Wire format:  b"cc1" + nonce(12) + ciphertext+tag.

The master key comes from `settings.FIELD_ENCRYPTION_KEY` (32 bytes, base64 or
hex). A future KMS integration swaps `MASTER_KEY_PROVIDER` — the derivation and
wire format are unchanged. `Tenant.encryption_key_ref` is reserved for that
per-tenant-KMS-key path.
"""
from __future__ import annotations

import base64
import binascii
import os
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from django.conf import settings

_MAGIC = b"cc1"
_NONCE_LEN = 12


class FieldEncryptionNotConfigured(RuntimeError):
    pass


class FieldDecryptionError(RuntimeError):
    pass


def _load_master_key() -> bytes:
    raw = getattr(settings, "FIELD_ENCRYPTION_KEY", "") or os.getenv("FIELD_ENCRYPTION_KEY", "")
    if not raw:
        raise FieldEncryptionNotConfigured(
            "settings.FIELD_ENCRYPTION_KEY is not set — required to read/write "
            "encrypted (PII/PHI) fields. Generate 32 random bytes, base64-encode."
        )
    for decode in (base64.b64decode, binascii.unhexlify):
        try:
            key = decode(raw)
            if len(key) == 32:
                return key
        except (binascii.Error, ValueError):
            continue
    raise FieldEncryptionNotConfigured(
        "FIELD_ENCRYPTION_KEY must decode (base64 or hex) to exactly 32 bytes."
    )


#: swap for a KMS-backed provider in production
MASTER_KEY_PROVIDER = _load_master_key


@lru_cache(maxsize=2048)
def _tenant_dek(tenant_id: str) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=str(tenant_id).encode("utf-8"),
        info=b"cybercom-field-dek-v1",
    )
    return hkdf.derive(MASTER_KEY_PROVIDER())


def encrypt(tenant_id, plaintext: str) -> bytes:
    if plaintext is None or plaintext == "":
        return b""
    aes = AESGCM(_tenant_dek(str(tenant_id)))
    nonce = os.urandom(_NONCE_LEN)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return _MAGIC + nonce + ct


def decrypt(tenant_id, blob: bytes) -> str:
    if not blob:
        return ""
    if not blob.startswith(_MAGIC):
        raise FieldDecryptionError("bad ciphertext header (wrong key era or corruption)")
    body = blob[len(_MAGIC):]
    nonce, ct = body[:_NONCE_LEN], body[_NONCE_LEN:]
    try:
        return AESGCM(_tenant_dek(str(tenant_id))).decrypt(nonce, ct, None).decode("utf-8")
    except Exception as exc:  # InvalidTag etc.
        raise FieldDecryptionError(f"decryption failed for tenant {tenant_id}: {exc}") from exc


def is_encrypted(blob) -> bool:
    return isinstance(blob, (bytes, bytearray)) and bytes(blob).startswith(_MAGIC)


def blind_index(value: str) -> str:
    """Deterministic HMAC over a value for exact-match lookup on an encrypted
    column (the `<field>_bidx` sidecar). Keyed by the master key so it is not a
    plain hash of the plaintext."""
    import hashlib
    import hmac

    return hmac.new(
        MASTER_KEY_PROVIDER(), (value or "").strip().lower().encode("utf-8"), hashlib.sha256
    ).hexdigest()
