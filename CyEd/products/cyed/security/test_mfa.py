"""
MFA: enrolment, verification, replay, lockout, step-up, and secret containment.

This app exists because an ST4S auditor rejected CyEd for having no second
factor. A second factor that leaks its secret or accepts a replayed code is
worse than none — it creates false assurance. These tests attack it.
"""

import time
import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.security import services, totp as totp_lib
from products.cyed.security.models import MfaEnrollment, MfaSession, SecurityEvent


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="ada@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def _enrol(client):
    r = client.post("/api/v1/security/mfa/enroll/", {"label": "iPhone"}, format="json")
    assert r.status_code == 201, r.data
    return r.data["secret"]


def _confirm(client, secret):
    return client.post("/api/v1/security/mfa/confirm/",
                       {"code": totp_lib.totp(secret)}, format="json")


# ── TOTP algorithm ───────────────────────────────────────────────────────────
def test_totp_matches_rfc4226_reference_vector():
    """RFC 4226 Appendix D: the published secret must produce the published codes."""
    import base64

    secret = base64.b32encode(b"12345678901234567890").decode()
    expected = ["755224", "287082", "359152", "969429", "338314"]
    for counter, code in enumerate(expected):
        assert totp_lib.hotp(secret, counter) == code


def test_verify_accepts_clock_skew_within_one_step():
    secret = totp_lib.generate_secret()
    now = time.time()
    assert totp_lib.verify(secret, totp_lib.totp(secret, now - 30), at=now) is not None
    assert totp_lib.verify(secret, totp_lib.totp(secret, now + 30), at=now) is not None
    # Two steps away is outside the window.
    assert totp_lib.verify(secret, totp_lib.totp(secret, now - 90), at=now) is None


def test_verify_rejects_a_replayed_time_step():
    """A code seen over someone's shoulder must be useless within its own window."""
    secret = totp_lib.generate_secret()
    now = time.time()
    counter = totp_lib.verify(secret, totp_lib.totp(secret, now), at=now)
    assert counter is not None
    assert totp_lib.verify(secret, totp_lib.totp(secret, now), at=now,
                           after_counter=counter) is None


def test_malformed_codes_are_rejected():
    secret = totp_lib.generate_secret()
    for bad in ("", "abcdef", "12345", "1234567", None):
        assert totp_lib.verify(secret, bad) is None


# ── Enrolment flow ───────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_enrol_confirm_and_verify(client_for, tenant_id):
    me = client_for(["teacher"])
    assert me.get("/api/v1/security/mfa/status/").data["enrolled"] is False

    secret = _enrol(me)
    # Unconfirmed enrolment grants nothing.
    assert me.get("/api/v1/security/mfa/status/").data["confirmed"] is False

    r = _confirm(me, secret)
    assert r.status_code == 200, r.data
    assert len(r.data["backup_codes"]) == services.BACKUP_CODE_COUNT

    status = me.get("/api/v1/security/mfa/status/").data
    assert status["confirmed"] is True
    assert status["backup_codes_remaining"] == services.BACKUP_CODE_COUNT


@pytest.mark.django_db
def test_confirm_rejects_a_wrong_code(client_for, tenant_id):
    me = client_for(["teacher"])
    _enrol(me)
    r = me.post("/api/v1/security/mfa/confirm/", {"code": "000000"}, format="json")
    assert r.status_code == 400
    assert MfaEnrollment.objects.get(tenant_id=tenant_id).confirmed is False


@pytest.mark.django_db
def test_cannot_re_enrol_while_confirmed(client_for, tenant_id):
    me = client_for(["teacher"])
    _confirm(me, _enrol(me))
    r = me.post("/api/v1/security/mfa/enroll/", {}, format="json")
    assert r.status_code == 400
    assert "already active" in r.data["detail"].lower()


# ── Secret containment ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_secret_never_appears_in_any_listing(client_for, tenant_id):
    """
    The shared secret leaves the server once, at enrolment. If it appears
    anywhere else the second factor is worthless.
    """
    me = client_for(["tenant_admin"])
    secret = _enrol(me)
    _confirm(me, secret)

    for url in ("/api/v1/security/enrollments/",
                "/api/v1/security/events/",
                "/api/v1/security/login-attempts/",
                "/api/v1/security/mfa/status/"):
        body = me.get(url).content.decode()
        # The property that matters is the secret VALUE never reappearing.
        # (Audit text may legitimately contain the word "secret".)
        assert secret not in body, f"secret leaked via {url}"
        # Nor should the field be serialized at all.
        assert '"secret"' not in body, f"secret field exposed via {url}"


@pytest.mark.django_db
def test_secret_is_encrypted_at_rest(monkeypatch, client_for, tenant_id):
    from cryptography.fernet import Fernet
    from django.db import connection

    monkeypatch.setenv("CYED_FIELD_KEY", Fernet.generate_key().decode())
    me = client_for(["teacher"])
    secret = _enrol(me)

    with connection.cursor() as cur:
        cur.execute("SELECT secret FROM cyed_mfa_enrollments")
        raw = cur.fetchone()[0]
    assert secret not in raw, "TOTP secret stored in plaintext"
    assert raw.startswith(("enc:v1:", "enc:v2:"))


@pytest.mark.django_db
def test_no_secret_material_in_audit_trail(client_for, tenant_id):
    me = client_for(["teacher"])
    secret = _enrol(me)
    r = _confirm(me, secret)
    codes = r.data["backup_codes"]

    trail = " ".join(
        f"{e.detail} {e.actor_email}" for e in SecurityEvent.objects.filter(tenant_id=tenant_id)
    )
    assert secret not in trail
    for code in codes:
        assert code not in trail


# ── Backup codes ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_backup_code_works_once(client_for, tenant_id):
    me = client_for(["teacher"])
    codes = _confirm(me, _enrol(me)).data["backup_codes"]

    first = me.post("/api/v1/security/mfa/verify/", {"code": codes[0]}, format="json")
    assert first.status_code == 200
    assert first.data["method"] == "backup"

    again = me.post("/api/v1/security/mfa/verify/", {"code": codes[0]}, format="json")
    assert again.status_code == 400, "a backup code was accepted twice"


@pytest.mark.django_db
def test_regenerating_backup_codes_invalidates_the_old_set(client_for, tenant_id):
    me = client_for(["teacher"])
    secret = _enrol(me)
    old = _confirm(me, secret).data["backup_codes"]

    time.sleep(1)  # ensure a fresh TOTP step (previous one is watermarked)
    r = me.post("/api/v1/security/mfa/backup-codes/",
                {"code": totp_lib.totp(secret, time.time() + 30)}, format="json")
    assert r.status_code == 200, r.data
    assert set(r.data["backup_codes"]).isdisjoint(set(old))

    stale = me.post("/api/v1/security/mfa/verify/", {"code": old[0]}, format="json")
    assert stale.status_code == 400


# ── Lockout ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_repeated_failures_lock_the_account(client_for, tenant_id):
    me = client_for(["teacher"])
    _confirm(me, _enrol(me))

    for _ in range(services.MAX_FAILURES):
        me.post("/api/v1/security/mfa/verify/", {"code": "000000"}, format="json")

    blocked = me.post("/api/v1/security/mfa/verify/", {"code": "000000"}, format="json")
    assert blocked.status_code == 429
    assert SecurityEvent.objects.filter(tenant_id=tenant_id,
                                        event_type=SecurityEvent.LOCKOUT).exists()


@pytest.mark.django_db
def test_success_clears_the_failure_streak(client_for, tenant_id):
    me = client_for(["teacher"])
    secret = _enrol(me)
    _confirm(me, secret)

    for _ in range(services.MAX_FAILURES - 1):
        me.post("/api/v1/security/mfa/verify/", {"code": "000000"}, format="json")
    assert services.recent_failures(tenant_id, "ada@cyed.edu.au") == services.MAX_FAILURES - 1

    me.post("/api/v1/security/mfa/verify/",
            {"code": totp_lib.totp(secret, time.time() + 30)}, format="json")
    assert services.recent_failures(tenant_id, "ada@cyed.edu.au") == 0


# ── One user must not touch another's MFA ────────────────────────────────────
@pytest.mark.django_db
def test_a_user_cannot_disable_someone_elses_mfa(client_for, tenant_id):
    """
    Every endpoint derives its subject from the token, so there is no parameter
    to point at another account. Proven by acting as a second user.
    """
    ada = client_for(["teacher"], email="ada@cyed.edu.au")
    secret = _enrol(ada)
    _confirm(ada, secret)

    bob = client_for(["tenant_admin"], email="bob@cyed.edu.au")
    # Bob supplies Ada's valid code — it must not disable Ada's MFA, because the
    # endpoint acts on Bob.
    r = bob.post("/api/v1/security/mfa/disable/",
                 {"code": totp_lib.totp(secret, time.time() + 30), "email": "ada@cyed.edu.au"},
                 format="json")
    assert r.status_code == 400
    assert MfaEnrollment.objects.filter(tenant_id=tenant_id,
                                        user_email="ada@cyed.edu.au", confirmed=True).exists()


@pytest.mark.django_db
def test_non_admin_sees_only_their_own_enrollment(client_for, tenant_id):
    ada = client_for(["teacher"], email="ada@cyed.edu.au")
    _confirm(ada, _enrol(ada))
    bob = client_for(["teacher"], email="bob@cyed.edu.au")
    _confirm(bob, _enrol(bob))

    rows = bob.get("/api/v1/security/enrollments/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert all(r["user_email"] == "bob@cyed.edu.au" for r in rows)


@pytest.mark.django_db
def test_audit_trail_is_leadership_only(client_for, tenant_id):
    teacher = client_for(["teacher"])
    rows = teacher.get("/api/v1/security/events/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert rows == []


# ── Disable + step-up ────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_disable_requires_a_valid_code(client_for, tenant_id):
    """A stolen bearer token alone must not strip the second factor."""
    me = client_for(["teacher"])
    secret = _enrol(me)
    _confirm(me, secret)

    assert me.post("/api/v1/security/mfa/disable/", {"code": "000000"},
                   format="json").status_code == 400
    assert MfaEnrollment.objects.filter(tenant_id=tenant_id, confirmed=True).exists()

    ok = me.post("/api/v1/security/mfa/disable/",
                 {"code": totp_lib.totp(secret, time.time() + 30)}, format="json")
    assert ok.status_code == 200
    assert not MfaEnrollment.objects.filter(tenant_id=tenant_id).exists()


@pytest.mark.django_db
def test_step_up_window_opens_on_verify_and_is_required_otherwise(client_for, tenant_id):
    me = client_for(["teacher"])
    secret = _enrol(me)
    _confirm(me, secret)

    assert services.has_recent_mfa(tenant_id, "ada@cyed.edu.au") is True

    MfaSession.objects.filter(tenant_id=tenant_id).update(revoked_at="2020-01-01T00:00:00Z")
    assert services.has_recent_mfa(tenant_id, "ada@cyed.edu.au") is False

    me.post("/api/v1/security/mfa/verify/",
            {"code": totp_lib.totp(secret, time.time() + 30)}, format="json")
    assert services.has_recent_mfa(tenant_id, "ada@cyed.edu.au") is True


@pytest.mark.django_db
def test_step_up_permission_fails_closed_without_enrolment(client_for, tenant_id, rf):
    """A user with no MFA cannot satisfy step-up — that is intended."""
    from products.cyed.security.stepup import RequiresRecentMfa

    request = rf.post("/x")
    request.auth_claims = {"sub": "x"}
    request.user_session = {"email": "nobody@cyed.edu.au", "roles": ["teacher"]}
    request.tenant_id = tenant_id
    assert RequiresRecentMfa().has_permission(request, None) is False


@pytest.mark.django_db
def test_security_events_are_append_only(tenant_id):
    e = services.record_event(tenant_id, SecurityEvent.MFA_VERIFIED, actor="a@b.com")
    e.detail = "tampered"
    with pytest.raises(ValueError):
        e.save()
    with pytest.raises(ValueError):
        e.delete()
