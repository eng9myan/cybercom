"""
Transparent field-level encryption at rest for CyEd.

`EncryptedTextField` / `EncryptedCharField` encrypt their value on the way into
the database and decrypt on the way out, using a Fernet key from the
``CYED_FIELD_KEY`` environment variable (URL-safe base64, 32 bytes — generate
with ``Fernet.generate_key()``).

Design goals:
  - **Reversible, keyed-at-rest**: sensitive health/wellbeing free text is
    ciphertext in the DB. Losing the DB dump does not leak medical notes.
  - **Zero-config dev**: with no key set, values are stored as plaintext so the
    dev/test SQLite flow keeps working. A stored ``enc:v1:`` prefix marks
    ciphertext so we never double-encrypt and can detect key loss.
  - **Key rotation friendly**: ``CYED_FIELD_KEY`` may hold multiple
    whitespace/comma-separated keys; the first encrypts, all are tried on
    decrypt (MultiFernet semantics).
"""

import os

from django.db import models

# Ciphertext is version-tagged so the algorithm can change without orphaning
# stored data:
#   enc:v1:  Fernet (AES-128-CBC + HMAC-SHA256) — legacy, still readable
#   enc:v2:  AES-256-GCM — what new writes use
# ST4S/ISM expect AES-256, which v1 did not meet. v1 is never written any more
# but must stay decryptable: a row encrypted before the upgrade is still
# somebody's medical record.
_PREFIX_V1 = "enc:v1:"
_PREFIX_V2 = "enc:v2:"
_PREFIXES = (_PREFIX_V1, _PREFIX_V2)

_NONCE_BYTES = 12  # 96-bit nonce, the size AES-GCM is specified for
_HKDF_INFO = b"cyed-field-encryption-v2"


def _keys():
    raw = os.environ.get("CYED_FIELD_KEY", "").strip()
    if not raw:
        return []
    return [k for k in raw.replace(",", " ").split() if k]


def _fernet():
    """Legacy v1 reader. Kept only to decrypt data written before the upgrade."""
    keys = _keys()
    if not keys:
        return None
    from cryptography.fernet import Fernet, MultiFernet

    try:
        fernets = [Fernet(k.encode() if isinstance(k, str) else k) for k in keys]
    except Exception:
        # A v2-only key need not be a valid Fernet key.
        return None
    return MultiFernet(fernets) if len(fernets) > 1 else fernets[0]


def _aes_keys() -> list[bytes]:
    """
    256-bit keys derived from the configured key material.

    HKDF-SHA256 is used so any key string (including an existing 32-byte Fernet
    key) yields a proper 256-bit AES key, and so the field-encryption key is
    domain-separated from any other use of the same secret. The first key
    encrypts; all keys are tried on decrypt, which is what makes rotation
    possible: add the new key first, re-encrypt, then drop the old one.
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    out = []
    for k in _keys():
        material = k.encode() if isinstance(k, str) else k
        out.append(
            HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_HKDF_INFO).derive(material)
        )
    return out


def encrypt_str(value: str) -> str:
    if value is None or value == "":
        return value
    if value.startswith(_PREFIXES):
        return value  # already ciphertext
    keys = _aes_keys()
    if not keys:
        return value  # dev: no key configured → plaintext
    import base64
    import secrets

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = secrets.token_bytes(_NONCE_BYTES)
    # GCM is authenticated: tampering with the ciphertext fails decryption
    # rather than silently returning garbage.
    blob = nonce + AESGCM(keys[0]).encrypt(nonce, value.encode(), None)
    return _PREFIX_V2 + base64.urlsafe_b64encode(blob).decode()


def decrypt_str(value: str) -> str:
    if value is None or value == "" or not value.startswith(_PREFIXES):
        return value

    if value.startswith(_PREFIX_V2):
        keys = _aes_keys()
        if not keys:
            # Ciphertext present but no key — return as-is rather than crash reads.
            return value
        import base64

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        try:
            blob = base64.urlsafe_b64decode(value[len(_PREFIX_V2):].encode())
            nonce, ct = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
        except Exception:
            return value
        for key in keys:  # try every key so rotation works
            try:
                return AESGCM(key).decrypt(nonce, ct, None).decode()
            except Exception:
                continue
        return value

    # Legacy v1 (Fernet).
    f = _fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value[len(_PREFIX_V1):].encode()).decode()
    except Exception:
        return value


class _EncryptedMixin:
    """Shared crypto behaviour for encrypted DB columns (stored as TEXT/VARCHAR)."""

    def from_db_value(self, value, expression, connection):
        return decrypt_str(value)

    def to_python(self, value):
        # Called on deserialization / forms; decrypt if we got ciphertext.
        return decrypt_str(super().to_python(value)) if value is not None else value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_str(value)


class EncryptedTextField(_EncryptedMixin, models.TextField):
    pass


class EncryptedCharField(_EncryptedMixin, models.CharField):
    pass
