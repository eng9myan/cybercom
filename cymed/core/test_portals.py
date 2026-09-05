"""Server-rendered portal shells: reachability, i18n/RTL, no fabricated data."""

import pytest
from django.test import Client
from django.utils import translation


@pytest.fixture
def client():
    return Client()


# ── Reachability (the tenant middleware used to 400 these before the view) ──


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/", "/patient-portal/", "/provider-portal/", "/patient-app/"])
def test_portal_pages_render_without_a_tenant(client, path):
    resp = client.get(path)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_dashboard_shows_signed_out_state_not_fake_numbers(client):
    body = client.get("/").content.decode()
    assert "Sign in to see live network data" in body
    # the old mockup's fabricated figures must be gone
    assert "12,847" not in body
    assert "Al-Amal Hospital" not in body


@pytest.mark.django_db
def test_patient_portal_has_no_fabricated_pii(client):
    body = client.get("/patient-portal/").content.decode()
    assert "Sign in to your patient portal" in body
    assert "Sarah Al-Rashid" not in body
    assert "8847219" not in body
    assert "Penicillin, Peanuts" not in body


@pytest.mark.django_db
def test_provider_portal_has_no_fabricated_pii(client):
    body = client.get("/provider-portal/").content.decode()
    assert "Sign in to your provider portal" in body
    assert "Dr. Kareem Hassan" not in body
    assert "Ahmad Saleh" not in body
    assert "Potassium 6.8" not in body


# ── i18n / RTL ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_default_locale_is_ltr_english(client):
    body = client.get("/").content.decode()
    assert 'dir="ltr"' in body
    assert 'lang="en"' in body
    assert "Command Center" in body


@pytest.mark.django_db
def test_arabic_locale_renders_rtl_and_translated(client):
    resp = client.get("/", headers={"accept-language": "ar"})
    body = resp.content.decode()
    assert 'dir="rtl"' in body
    assert 'lang="ar"' in body
    assert "مركز القيادة" in body            # "Command Center"
    assert "لوحة التحكم" in body              # "Dashboard" nav link
    assert "Command Center" not in body      # English string fully replaced


@pytest.mark.django_db
def test_set_language_view_switches_the_session_locale(client):
    resp = client.post("/i18n/setlang/", {"language": "ar", "next": "/"})
    assert resp.status_code in (302, 200)
    body = client.get("/").content.decode()
    assert 'dir="rtl"' in body
    assert "بوابة المريض" in body            # "Patient Portal"


def test_arabic_catalog_covers_every_template_trans_string():
    """Guard against a template adding a {% trans %} that build_ar_locale.py
    was never updated for — a missing key silently falls back to English
    inside an otherwise-Arabic page."""
    import re
    from pathlib import Path

    from scripts.build_ar_locale import AR

    tmpl_dir = Path(__file__).resolve().parent.parent / "templates"
    pat = re.compile(r'{%\s*trans\s+"([^"]+)"\s*%}')
    missing = set()
    for html in tmpl_dir.rglob("*.html"):
        for msgid in pat.findall(html.read_text(encoding="utf-8")):
            if msgid not in AR:
                missing.add(msgid)
    assert not missing, f"no Arabic translation for: {sorted(missing)}"
