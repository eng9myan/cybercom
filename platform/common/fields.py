"""
EncryptedText — a model field that transparently encrypts its value per-tenant
(canonical-data-model-v1.md §2.3).

    class Employee(BaseModel):
        national_id = EncryptedText(classification="national_id", blind_index=True)
        iban        = EncryptedText(classification="financial_id")

- Stored in the DB as a `bytea` (BinaryField) — the wire format from
  platform.security.crypto (b"cc1" + nonce + AES-256-GCM ciphertext).
- Encrypted on write with the DEK derived from the ambient tenant
  (`platform.common.tenant_context`); a write with no tenant context raises.
- Decrypted on read when a tenant context is present; without one, reads yield
  the mask "••••" rather than leaking or crashing a list view.
- `blind_index=True` adds a companion `<name>_bidx` CharField holding an HMAC of
  the (normalised) plaintext, so exact-match lookups still work:
      Employee.objects.filter(national_id_bidx=blind_index(value))
- Registers itself in `platform.common.pii_registry` for the DPIA / residency
  lint / DSAR tooling.
"""
from __future__ import annotations

import logging

from django.db import models

from platform.common.pii_registry import register_pii_field
from platform.common.tenant_context import TenantContextMissing, get_current_tenant
from platform.security.crypto import blind_index, decrypt, encrypt, is_encrypted

logger = logging.getLogger("platform.common.fields")

MASK = "••••"  # ••••


class EncryptedText(models.BinaryField):
    description = "Per-tenant AES-256-GCM encrypted text"

    def __init__(self, *args, classification: str = "pii", blind_index: bool = False, **kwargs):
        self.classification = classification
        self.blind_index = blind_index
        kwargs.setdefault("editable", True)
        kwargs.setdefault("blank", True)
        # values are variable-length ciphertext; no max_length on bytea
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["classification"] = self.classification
        if self.blind_index:
            kwargs["blind_index"] = True
        return name, path, args, kwargs

    # ── companion blind-index column + registry entry ──────────────────────
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        if not cls._meta.abstract:
            register_pii_field(
                f"{cls._meta.app_label}.{cls.__name__}", name,
                self.classification, self.blind_index,
            )
        if self.blind_index and not cls._meta.abstract:
            bidx = models.CharField(max_length=64, db_index=True, null=True, blank=True, editable=False)
            cls.add_to_class(f"{name}_bidx", bidx)
        self._name = name

    # ── read ──────────────────────────────────────────────────────────────
    def from_db_value(self, value, expression, connection):
        if value in (None, b"", ""):
            return value if value is None else ""
        raw = bytes(value)
        if not is_encrypted(raw):
            return raw.decode("utf-8", "replace")  # legacy plaintext, pre-migration
        tid = get_current_tenant()
        if tid is None:
            logger.warning("encrypted field read with no tenant context — masking")
            return MASK
        return decrypt(tid, raw)

    def to_python(self, value):
        if value is None or isinstance(value, str):
            return value
        if isinstance(value, (bytes, bytearray)):
            b = bytes(value)
            return b.decode("utf-8", "replace") if not is_encrypted(b) else b
        return str(value)

    # ── write ─────────────────────────────────────────────────────────────
    def get_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)) and is_encrypted(bytes(value)):
            return bytes(value)  # already-encrypted (e.g. re-save of a loaded row)
        if value == "":
            return b""
        tid = get_current_tenant()
        if tid is None:
            raise TenantContextMissing(
                f"writing encrypted field '{getattr(self, '_name', '?')}' with no tenant "
                f"context — pass tenant_id= / wrap in tenant_context(...)."
            )
        return encrypt(tid, str(value))

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if self.blind_index:
            bidx_val = blind_index(str(value)) if value not in (None, "", MASK) and not (
                isinstance(value, (bytes, bytearray)) and is_encrypted(bytes(value))
            ) else None
            setattr(model_instance, f"{self.attname}_bidx", bidx_val)
        return super().pre_save(model_instance, add)
