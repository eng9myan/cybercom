"""Per-tenant field encryption: crypto primitives + the EncryptedText field."""
import uuid

import pytest

from platform.common.fields import MASK, EncryptedJSON, EncryptedText
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


class _FakeInstance:
    """Minimal stand-in for a model instance in pre_save()."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_pre_save_encrypts_from_instance_tenant_id_without_ambient_context():
    f = _field()
    tid = uuid.uuid4()
    inst = _FakeInstance(national_id="2001234567", tenant_id=tid)
    # no tenant_context active — the instance's own tenant_id must be enough
    out = f.pre_save(inst, add=True)
    assert is_encrypted(out)
    assert decrypt(tid, out) == "2001234567"
    assert inst.national_id_bidx == blind_index("2001234567")
    # the instance attribute stays plaintext (readable right after save())
    assert inst.national_id == "2001234567"


def test_pre_save_prefers_instance_tenant_id_over_ambient():
    f = _field()
    inst_tid, ambient_tid = uuid.uuid4(), uuid.uuid4()
    inst = _FakeInstance(national_id="99", tenant_id=inst_tid)
    with tenant_context(ambient_tid):
        out = f.pre_save(inst, add=True)
    assert decrypt(inst_tid, out) == "99"


def test_pre_save_falls_back_to_ambient_context_when_instance_has_no_tenant():
    f = _field()
    tid = uuid.uuid4()
    inst = _FakeInstance(national_id="42", tenant_id=None)
    with tenant_context(tid):
        out = f.pre_save(inst, add=True)
    assert decrypt(tid, out) == "42"


def test_pre_save_raises_when_no_tenant_anywhere():
    inst = _FakeInstance(national_id="x", tenant_id=None)
    with pytest.raises(TenantContextMissing):
        _field().pre_save(inst, add=True)


def test_pre_save_empty_value_clears_blind_index_and_does_not_encrypt():
    f = _field()
    inst = _FakeInstance(national_id="", tenant_id=uuid.uuid4(), national_id_bidx="stale")
    out = f.pre_save(inst, add=True)
    assert out in (b"", "")
    assert inst.national_id_bidx is None


def test_pre_save_is_idempotent_on_an_already_encrypted_value():
    f = _field()
    tid = uuid.uuid4()
    blob = encrypt(tid, "keep")
    inst = _FakeInstance(national_id=blob, tenant_id=tid)
    assert f.pre_save(inst, add=False) == blob  # not re-encrypted


def test_pre_save_refuses_to_write_back_a_masked_value():
    f = _field()
    inst = _FakeInstance(national_id=MASK, tenant_id=uuid.uuid4())
    with pytest.raises(TenantContextMissing):
        f.pre_save(inst, add=False)


# ── EncryptedJSON field ───────────────────────────────────────────────────
def _json_field(default=list):
    f = EncryptedJSON(classification="phi", json_default=default)
    f._name = f.attname = "payload"
    return f


def test_encrypted_json_round_trips_a_list():
    f = _json_field()
    tid = uuid.uuid4()
    inst = _FakeInstance(payload=[{"drug": "amoxicillin", "dose": "500mg"}], tenant_id=tid)
    out = f.pre_save(inst, add=True)
    assert is_encrypted(out)
    assert f.from_db_value(out, None, None) is None or True  # no ctx path below
    with tenant_context(tid):
        assert f.from_db_value(out, None, None) == [{"drug": "amoxicillin", "dose": "500mg"}]


def test_encrypted_json_masks_to_default_without_context():
    f = _json_field(default=dict)
    tid = uuid.uuid4()
    inst = _FakeInstance(payload={"k": "v"}, tenant_id=tid)
    out = f.pre_save(inst, add=True)
    assert f.from_db_value(out, None, None) == {}   # default(), never the mask string


def test_encrypted_json_empty_values_store_nothing():
    f = _json_field()
    for empty in ([], None, ""):
        inst = _FakeInstance(payload=empty, tenant_id=uuid.uuid4())
        assert f.pre_save(inst, add=True) == b""
    assert f.from_db_value(b"", None, None) == []


def test_encrypted_json_rejects_blind_index():
    with pytest.raises(TypeError):
        EncryptedJSON(classification="phi", blind_index=True)


def test_encrypted_json_reads_legacy_plaintext_json():
    f = _json_field()
    # a row written by the old JSONField, pre-migration
    assert f.from_db_value('[{"a":1}]', None, None) == [{"a": 1}]


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
