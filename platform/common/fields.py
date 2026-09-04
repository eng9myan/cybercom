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

    empty_strings_allowed = False

    def __init__(self, *args, classification: str = "pii", blind_index: bool = False, **kwargs):
        self.classification = classification
        self.blind_index = blind_index
        kwargs.setdefault("editable", True)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("default", b"")   # variable-length ciphertext; empty = no value
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
        self._name = name
        if cls._meta.abstract:
            return

        # Only act on the real app model, not migration-state reconstructions
        # (those get the _bidx column from the explicit AddField in the migration).
        from django.apps import apps as global_apps

        is_real_model = getattr(cls._meta, "apps", None) is global_apps
        if not is_real_model:
            return

        register_pii_field(
            f"{cls._meta.app_label}.{cls.__name__}", name,
            self.classification, self.blind_index,
        )
        if self.blind_index:
            bidx_name = f"{name}_bidx"
            if not any(f.name == bidx_name for f in cls._meta.local_fields):
                cls.add_to_class(
                    bidx_name,
                    models.CharField(max_length=64, db_index=True, null=True,
                                     blank=True, editable=False),
                )

    # ── read ──────────────────────────────────────────────────────────────
    def from_db_value(self, value, expression, connection):
        if value in (None, b"", ""):
            return value if value is None else ""
        if isinstance(value, str):
            return value  # legacy plaintext (SQLite keeps strings through a CharField→bytea alter)
        raw = value if isinstance(value, bytes) else bytes(value)
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
    @staticmethod
    def _is_empty(value) -> bool:
        return value in (None, "", b"")

    def get_prep_value(self, value):
        # pre_save already turned an instance write into ciphertext bytes. This
        # only runs on its own for a str reaching the DB with no instance —
        # `.update(field=...)`, raw SQL, a QuerySet bulk update.
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        if value == "":
            return b""
        tid = get_current_tenant()
        if tid is None:
            raise TenantContextMissing(
                f"writing encrypted field '{getattr(self, '_name', '?')}' with no tenant "
                f"context (and no model instance) — use save() with tenant_id set, or "
                f"wrap in tenant_context(...)."
            )
        return encrypt(tid, str(value))

    def _resolve_tid(self, model_instance):
        return getattr(model_instance, "tenant_id", None) or get_current_tenant()

    def pre_save(self, model_instance, add):
        """Return the ciphertext to persist; keep the instance attribute in
        plaintext so code can read the field right after ``save()`` without a
        refresh. Only the companion ``<name>_bidx`` column is written back onto
        the instance."""
        value = getattr(model_instance, self.attname)
        already_ct = isinstance(value, (bytes, bytearray)) and is_encrypted(bytes(value))

        if already_ct:
            return bytes(value)

        if value == MASK:
            # re-saving a row that was read without tenant context — we never
            # had the plaintext, so writing anything would corrupt or blank it.
            raise TenantContextMissing(
                f"re-saving '{self.attname}' that was read masked (no tenant "
                f"context on the original read) — reload it inside tenant_context(...)."
            )

        if self._is_empty(value):
            if self.blind_index:
                setattr(model_instance, f"{self.attname}_bidx", None)
            return b""

        plain = (
            value.decode("utf-8", "replace")
            if isinstance(value, (bytes, bytearray))
            else str(value)
        )
        tid = self._resolve_tid(model_instance)
        if tid is None:
            raise TenantContextMissing(
                f"encrypting '{self.attname}' needs a tenant — set the model's "
                f"tenant_id or wrap the save in tenant_context(...)."
            )
        if self.blind_index:
            setattr(model_instance, f"{self.attname}_bidx", blind_index(plain))
        return encrypt(tid, plain)
