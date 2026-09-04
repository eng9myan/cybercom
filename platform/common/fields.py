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

import json
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

    # ── plaintext <-> stored-string hooks (overridden by EncryptedJSON) ────
    def _to_plaintext(self, value) -> str:
        """Python value -> the string that gets encrypted."""
        return value if isinstance(value, str) else str(value)

    def _from_plaintext(self, text: str):
        """Decrypted string -> the Python value handed to the caller."""
        return text

    _EMPTY = ""       # what an absent value reads back as

    def _masked_read_value(self):
        """What a read with no tenant context yields (never the plaintext)."""
        return MASK

    def _is_masked_read(self, value) -> bool:
        """True when `value` on an instance is a mask sentinel from a no-context
        read (so re-saving it would corrupt the column)."""
        return value == MASK

    # ── read ──────────────────────────────────────────────────────────────
    def from_db_value(self, value, expression, connection):
        if value in (None, b"", ""):
            return None if value is None else self._EMPTY
        if isinstance(value, str):
            return self._from_plaintext(value)  # legacy plaintext (SQLite CharField→bytea alter)
        raw = value if isinstance(value, bytes) else bytes(value)
        if not is_encrypted(raw):
            return self._from_plaintext(raw.decode("utf-8", "replace"))  # legacy plaintext
        tid = get_current_tenant()
        if tid is None:
            logger.warning("encrypted field read with no tenant context — masking")
            return self._masked_read_value()
        return self._from_plaintext(decrypt(tid, raw))

    def to_python(self, value):
        if value is None or isinstance(value, str):
            return value
        if isinstance(value, (bytes, bytearray)):
            b = bytes(value)
            return b.decode("utf-8", "replace") if not is_encrypted(b) else b
        return str(value)

    # ── write ─────────────────────────────────────────────────────────────
    def _is_empty(self, value) -> bool:
        return value is None or value == "" or value == b""

    def get_prep_value(self, value):
        # pre_save already turned an instance write into ciphertext bytes. This
        # only runs on its own for a value reaching the DB with no instance —
        # `.update(field=...)`, raw SQL, a QuerySet bulk update.
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        if self._is_empty(value):
            return b""
        tid = get_current_tenant()
        if tid is None:
            raise TenantContextMissing(
                f"writing encrypted field '{getattr(self, '_name', '?')}' with no tenant "
                f"context (and no model instance) — use save() with tenant_id set, or "
                f"wrap in tenant_context(...)."
            )
        return encrypt(tid, self._to_plaintext(value))

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

        if self._is_masked_read(value):
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
            else self._to_plaintext(value)
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


class EncryptedJSON(EncryptedText):
    """Per-tenant AES-256-GCM encrypted JSON.

    Stores a `dict` / `list` (anything `json.dumps` accepts) as an encrypted
    `bytea`, exactly like :class:`EncryptedText` but with a JSON codec on the
    plaintext. Blind indexing is not supported (structured values have no
    canonical exact-match form).

        prescriptions = EncryptedJSON(classification="phi")          # -> []
        agents_used   = EncryptedJSON(classification="phi", json_default=dict)

    A read with no tenant context yields `json_default()` (never the mask
    string), so callers that iterate the value keep working.
    """

    description = "Per-tenant AES-256-GCM encrypted JSON"

    def __init__(self, *args, json_default=list, **kwargs):
        if kwargs.pop("blind_index", False):
            raise TypeError("EncryptedJSON does not support blind_index")
        self.json_default = json_default
        kwargs.setdefault("default", json_default)
        super().__init__(*args, **kwargs)
        self.blind_index = False

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop("blind_index", None)
        if self.json_default is not list:
            kwargs["json_default"] = self.json_default
        return name, path, args, kwargs

    @property
    def _EMPTY(self):
        return self.json_default()

    def _masked_read_value(self):
        # No mask sentinel for JSON — an iterable default keeps callers working.
        return self.json_default()

    def _is_masked_read(self, value) -> bool:
        # A no-context JSON read is indistinguishable from a real empty value,
        # so this protection can't apply. Re-saving a JSON field read without a
        # tenant context writes json_default() — reload in context to be safe.
        return False

    def _to_plaintext(self, value) -> str:
        return json.dumps(value, separators=(",", ":"), default=str)

    def _from_plaintext(self, text: str):
        if text in ("", None):
            return self.json_default()
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            logger.warning("EncryptedJSON: undecodable payload — returning default")
            return self.json_default()

    def _is_empty(self, value) -> bool:
        return value is None or value == b"" or value == [] or value == {} or value == ""

    def to_python(self, value):
        if value is None or isinstance(value, (dict, list)):
            return value
        if isinstance(value, (bytes, bytearray)):
            b = bytes(value)
            return b if is_encrypted(b) else self._from_plaintext(b.decode("utf-8", "replace"))
        if isinstance(value, str):
            return self._from_plaintext(value)
        return value
