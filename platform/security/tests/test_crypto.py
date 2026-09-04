"""Per-tenant field encryption: crypto primitives + the EncryptedText field."""
import uuid

import pytest

from platform.common.fields import MASK, EncryptedText
from platform.common.pii_registry import registered_pii_fields
from platform.common.tenant_context import (
    TenantContextMissing,
    clear_current_tenant,
    tenant_context,
)
from platform.security.crypto import (
    FieldDecryptionError,
    blind_index,
    decrypt,
    encrypt,
    is_encrypted,
)


@pytest.fixture(autouse=True)
def _clean_ctx():
    clear_current_tenant()
    yield
    clear_current_tenant()


# ── crypto.py ─────────────────────────────────────────────────────────────
def test_roundtrip():
    t = uuid.uuid4()
    blob = encrypt(t, "2001234567")
    assert is_encrypted(blob) and blob != b"2001234567"
    assert decrypt(t, blob) == "2001234567"


def test_ciphertext_is_nondeterministic():
    t = uuid.uuid4()
    assert encrypt(t, "x") != encrypt(t, "x")  # random nonce per value


def test_wrong_tenant_cannot_decrypt():
    a, b = uuid.uuid4(), uuid.uuid4()
    blob = encrypt(a, "secret")
    with pytest.raises(FieldDecryptionError):
        decrypt(b, blob)


def test_tampered_ciphertext_rejected():
    t = uuid.uuid4()
    blob = bytearray(encrypt(t, "secret"))
    blob[-1] ^= 0x01
    with pytest.raises(FieldDecryptionError):
        decrypt(t, bytes(blob))


def test_blind_index_is_deterministic_and_normalised():
    assert blind_index("  Foo@Bar.com ") == blind_index("foo@bar.com")
    assert blind_index("a") != blind_index("b")
    assert len(blind_index("x")) == 64  # sha256 hex


def test_empty_values():
    t = uuid.uuid4()
    assert encrypt(t, "") == b""
    assert decrypt(t, b"") == ""


# ── EncryptedText field ───────────────────────────────────────────────────
def _field():
    f = EncryptedText(classification="national_id", blind_index=True)
    f._name = "national_id"
    f.attname = "national_id"
    return f


def test_get_prep_value_encrypts_with_context():
    f = _field()
    tid = uuid.uuid4()
    with tenant_context(tid):
        blob = f.get_prep_value("2001234567")
    assert is_encrypted(blob)
    assert decrypt(tid, blob) == "2001234567"


def test_get_prep_value_requires_context():
    with pytest.raises(TenantContextMissing):
        _field().get_prep_value("2001234567")


def test_from_db_value_decrypts_with_context():
    f = _field()
    tid = uuid.uuid4()
    with tenant_context(tid):
        blob = f.get_prep_value("2001234567")
        assert f.from_db_value(blob, None, None) == "2001234567"


def test_from_db_value_masks_without_context():
    f = _field()
    tid = uuid.uuid4()
    with tenant_context(tid):
        blob = f.get_prep_value("2001234567")
    # no context now -> masked, never leaked
    assert f.from_db_value(blob, None, None) == MASK


def test_from_db_value_passes_through_legacy_plaintext():
    # a row written before the field was encrypted
    assert _field().from_db_value(b"legacy-plain", None, None) == "legacy-plain"


def test_reencrypting_an_already_encrypted_value_is_idempotent():
    f = _field()
    tid = uuid.uuid4()
    with tenant_context(tid):
        blob = f.get_prep_value("x")
        assert f.get_prep_value(blob) == blob  # not double-encrypted


@pytest.mark.django_db
def test_field_registers_itself_in_the_pii_map():
    # ar_ap / hr etc. haven't adopted EncryptedText yet; just assert the
    # registry mechanism works when a field is instantiated on a model.
    from django.db import models as djm

    class _Probe(djm.Model):
        secret = EncryptedText(classification="phi")

        class Meta:
            app_label = "platform_security"

    labels = {(f.model_label, f.field_name) for f in registered_pii_fields()}
    assert ("platform_security._Probe", "secret") in labels
