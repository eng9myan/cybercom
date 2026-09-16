"""
Notification transport.

The governing rule is that a message is only `sent` once a provider
acknowledged it. Most of these tests are about the ways that could quietly stop
being true — an unknown provider name, a missing phone number, a provider that
raises — and confirm each one lands on `failed` rather than `sent`.
"""

import os
import uuid

import pytest

from products.cyed.notifications import providers
from products.cyed.notifications.delivery import deliver, retry_failed
from products.cyed.notifications.models import Notification
from products.cyed.notifications.providers import (
    NotificationProviderError,
    UnconfiguredProvider,
)

pytestmark = pytest.mark.django_db


class RecordingSms(providers.SmsProvider):
    name = "recording"

    def __init__(self):
        self.sent = []

    def send(self, *, to, body):
        self.sent.append((to, body))
        return providers.DeliveryReceipt(reference="rec-123", provider=self.name)


class BrokenSms(providers.SmsProvider):
    name = "broken"

    def send(self, *, to, body):
        raise NotificationProviderError("carrier rejected the number")


class RecordingEmail(providers.EmailProvider):
    name = "recording"

    def __init__(self):
        self.sent = []

    def send(self, *, to, subject, body):
        self.sent.append((to, subject, body))
        return providers.DeliveryReceipt(reference="msg-1", provider=self.name)


@pytest.fixture
def sms_on(monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_SMS_ENABLED", "1")


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    providers.set_override("sms", None)
    providers.set_override("email", None)


def _note(tenant_id, **extra):
    body = {
        "tenant_id": tenant_id,
        "recipient_kind": "guardian",
        "recipient_name": "Hoa Tran",
        "recipient_email": "hoa@example.com",
        "recipient_phone": "+61400000000",
        "channel": "sms",
        "category": "attendance",
        "subject": "Attendance alert: Mia Tran",
        "body": "Mia was marked absent on 11 August.",
        "status": "queued",
    }
    body.update(extra)
    return Notification.objects.create(**body)


# ── the happy path ───────────────────────────────────────────────────────────
def test_an_sms_reaches_the_provider_and_is_marked_sent(tenant_id, sms_on):
    transport = RecordingSms()
    providers.set_override("sms", transport)

    note = deliver(_note(tenant_id))

    assert note.status == "sent"
    assert note.sent_at is not None
    assert transport.sent[0][0] == "+61400000000"
    # SMS has no subject line, so it is folded into the body.
    assert "Attendance alert" in transport.sent[0][1]


def test_the_provider_reference_is_kept(tenant_id, sms_on):
    """
    "I never got the text" has to be answerable from the carrier's own logs.
    """
    providers.set_override("sms", RecordingSms())
    note = deliver(_note(tenant_id))
    assert note.provider_reference == "rec-123"
    assert note.provider == "recording"


def test_email_goes_out_with_its_subject(tenant_id, monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_EMAIL_ENABLED", "1")
    transport = RecordingEmail()
    providers.set_override("email", transport)

    deliver(_note(tenant_id, channel="email"))

    to, subject, _body = transport.sent[0]
    assert to == "hoa@example.com"
    assert subject == "Attendance alert: Mia Tran"


# ── never falsely sent ───────────────────────────────────────────────────────
def test_a_provider_failure_is_recorded_as_failed_not_sent(tenant_id, sms_on):
    providers.set_override("sms", BrokenSms())
    note = deliver(_note(tenant_id))

    assert note.status == "failed"
    assert note.sent_at is None
    assert "carrier rejected" in note.error


def test_a_missing_phone_number_fails_rather_than_claiming_delivery(tenant_id, sms_on):
    providers.set_override("sms", RecordingSms())
    note = deliver(_note(tenant_id, recipient_phone=""))

    assert note.status == "failed"
    assert "No phone number" in note.error


def test_an_unknown_provider_name_fails_loudly(tenant_id, sms_on, monkeypatch):
    """
    A typo in the provider name must not degrade to console, or a school will
    believe its alerts are going out.
    """
    monkeypatch.setenv("CYED_NOTIFY_SMS_PROVIDER", "twilioo")
    note = deliver(_note(tenant_id))

    assert note.status == "failed"
    assert "not a known provider" in note.error


def test_enabling_a_channel_with_no_provider_set_fails(tenant_id, sms_on, monkeypatch):
    monkeypatch.delenv("CYED_NOTIFY_SMS_PROVIDER", raising=False)
    note = deliver(_note(tenant_id))

    assert note.status == "failed"
    assert "is not set" in note.error


def test_a_channel_with_no_adapter_says_so(tenant_id, monkeypatch):
    """
    WhatsApp, not push — push gained a real adapter. The property under test is
    unchanged: enabling a channel CyEd cannot deliver fails loudly rather than
    dropping the message.
    """
    monkeypatch.setenv("CYED_NOTIFY_WHATSAPP_ENABLED", "1")
    note = deliver(_note(tenant_id, channel="whatsapp"))

    assert note.status == "failed"
    assert "no whatsapp adapter" in note.error


# ── queued vs failed ─────────────────────────────────────────────────────────
def test_a_disabled_channel_queues_rather_than_fails(tenant_id, monkeypatch):
    """
    Queued is a configuration state the school chose; failed is something that
    went wrong. Conflating them buries real faults in noise.
    """
    monkeypatch.delenv("CYED_NOTIFY_SMS_ENABLED", raising=False)
    note = deliver(_note(tenant_id))

    assert note.status == "queued"
    assert note.error == ""


def test_in_app_needs_no_provider(tenant_id):
    note = deliver(_note(tenant_id, channel="in_app"))
    assert note.status == "sent"


# ── provider selection ───────────────────────────────────────────────────────
def test_twilio_without_credentials_refuses_to_construct(monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_SMS_PROVIDER", "twilio")
    for var in ("CYED_TWILIO_ACCOUNT_SID", "CYED_TWILIO_AUTH_TOKEN", "CYED_TWILIO_FROM"):
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(UnconfiguredProvider) as exc:
        providers.get_provider("sms")
    assert "CYED_TWILIO_ACCOUNT_SID" in str(exc.value)


def test_smtp_without_a_host_refuses_to_construct(monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_EMAIL_PROVIDER", "smtp")
    monkeypatch.delenv("CYED_SMTP_HOST", raising=False)

    with pytest.raises(UnconfiguredProvider):
        providers.get_provider("email")


def test_console_provider_works_for_local_development(monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_SMS_PROVIDER", "console")
    provider = providers.get_provider("sms")
    receipt = provider.send(to="+61400000000", body="hello")
    assert receipt.provider == "console"


def test_recipients_are_masked_in_logs():
    """Full phone numbers and addresses must not reach a log aggregator."""
    assert providers._mask("+61400123456") == "…3456"
    assert providers._mask("ab") == "…"


# ── retries ──────────────────────────────────────────────────────────────────
def test_retry_recovers_messages_after_an_outage(tenant_id, sms_on):
    providers.set_override("sms", BrokenSms())
    for _ in range(3):
        deliver(_note(tenant_id))
    assert Notification.objects.filter(tenant_id=tenant_id, status="failed").count() == 3

    providers.set_override("sms", RecordingSms())
    result = retry_failed(tenant_id)

    assert result == {"attempted": 3, "recovered": 3}
    assert Notification.objects.filter(tenant_id=tenant_id, status="sent").count() == 3


def test_retry_leaves_queued_messages_alone(tenant_id, monkeypatch):
    """A queued message is waiting on configuration, not on a retry."""
    monkeypatch.delenv("CYED_NOTIFY_SMS_ENABLED", raising=False)
    deliver(_note(tenant_id))

    assert retry_failed(tenant_id) == {"attempted": 0, "recovered": 0}
    assert Notification.objects.filter(tenant_id=tenant_id, status="queued").count() == 1
