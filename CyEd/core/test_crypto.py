"""
Field-level encryption tests. Verify that with CYED_FIELD_KEY set, sensitive
fields are ciphertext at rest (raw DB column carries the enc: prefix) yet read
back transparently as plaintext; and that with no key set the value is stored
as plaintext (dev fallback) without error.
"""

import uuid

import pytest
from cryptography.fernet import Fernet
from django.db import connection

from core.crypto import decrypt_str, encrypt_str
from products.cyed.health.models import HealthRecord
from products.cyed.sis.models import Student


def test_encrypt_roundtrip_with_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CYED_FIELD_KEY", key)
    token = encrypt_str("Peanut allergy — EpiPen")
    assert token.startswith("enc:v2:")  # AES-256-GCM
    assert "Peanut" not in token
    assert decrypt_str(token) == "Peanut allergy — EpiPen"


def test_encrypt_noop_without_key(monkeypatch):
    monkeypatch.delenv("CYED_FIELD_KEY", raising=False)
    assert encrypt_str("plain") == "plain"
    assert decrypt_str("plain") == "plain"


@pytest.mark.django_db
def test_health_field_ciphertext_at_rest(monkeypatch, tenant_id):
    monkeypatch.setenv("CYED_FIELD_KEY", Fernet.generate_key().decode())
    student = Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="B", year_level=7)
    rec = HealthRecord.objects.create(tenant_id=tenant_id, student=student,
                                      allergies="Bee stings", notes="Carries antihistamine")

    # Read back through the ORM → decrypted transparently.
    fetched = HealthRecord.objects.get(pk=rec.pk)
    assert fetched.allergies == "Bee stings"
    assert fetched.notes == "Carries antihistamine"

    # Raw column → ciphertext, not the plaintext. (One row in the fresh test DB;
    # UUID PK encoding differs across backends, so read the sole row directly.)
    with connection.cursor() as cur:
        cur.execute("SELECT allergies, notes FROM cyed_health_records")
        raw_allergies, raw_notes = cur.fetchone()
    assert raw_allergies.startswith(("enc:v1:", "enc:v2:"))
    assert "Bee stings" not in raw_allergies
    assert raw_notes.startswith(("enc:v1:", "enc:v2:"))


# ── AES-256-GCM (v2) ─────────────────────────────────────────────────────────
def test_new_writes_use_aes256_gcm(monkeypatch):
    """ST4S/ISM expect AES-256; Fernet (v1) is AES-128 and must no longer be written."""
    monkeypatch.setenv("CYED_FIELD_KEY", Fernet.generate_key().decode())
    token = encrypt_str("Peanut allergy - EpiPen")
    assert token.startswith("enc:v2:"), "new ciphertext is not AES-256-GCM"
    assert "Peanut" not in token
    assert decrypt_str(token) == "Peanut allergy - EpiPen"


def test_legacy_v1_ciphertext_still_decrypts(monkeypatch):
    """Rows written before the upgrade are still somebody's medical record."""
    key = Fernet.generate_key()
    monkeypatch.setenv("CYED_FIELD_KEY", key.decode())
    legacy = "enc:v1:" + Fernet(key).encrypt(b"Legacy note").decode()
    assert decrypt_str(legacy) == "Legacy note"


def test_tampering_is_detected(monkeypatch):
    """GCM is authenticated: a modified ciphertext must not decrypt to garbage."""
    monkeypatch.setenv("CYED_FIELD_KEY", Fernet.generate_key().decode())
    token = encrypt_str("Confidential")
    body = list(token[len("enc:v2:"):])
    body[10] = "A" if body[10] != "A" else "B"
    assert decrypt_str("enc:v2:" + "".join(body)) != "Confidential"


def test_key_rotation_reads_old_and_writes_new(monkeypatch):
    """Adding a new key first must not make existing data unreadable."""
    old = Fernet.generate_key().decode()
    monkeypatch.setenv("CYED_FIELD_KEY", old)
    token = encrypt_str("Rotate me")
    new = Fernet.generate_key().decode()
    monkeypatch.setenv("CYED_FIELD_KEY", new + " " + old)
    assert decrypt_str(token) == "Rotate me", "old data unreadable after rotation"
    fresh = encrypt_str("Written with the new key")
    monkeypatch.setenv("CYED_FIELD_KEY", new)
    assert decrypt_str(fresh) == "Written with the new key"


def test_nonce_is_unique_per_encryption(monkeypatch):
    """Reusing a nonce under the same key breaks GCM catastrophically."""
    monkeypatch.setenv("CYED_FIELD_KEY", Fernet.generate_key().decode())
    tokens = {encrypt_str("same plaintext") for _ in range(25)}
    assert len(tokens) == 25, "identical ciphertext produced - nonce reuse"
