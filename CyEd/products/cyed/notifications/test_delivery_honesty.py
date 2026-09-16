"""
Delivery must never claim success it cannot prove.

Regression for an audit finding: with the channel flag enabled but no provider
wired, delivery previously marked messages `sent`. For an absence alert that
means the school holds a record saying a guardian was notified when nobody was.
"""

import pytest

from products.cyed.notifications.delivery import deliver
from products.cyed.notifications.models import Notification


def _note(tenant_id, channel):
    return Notification.objects.create(
        tenant_id=tenant_id, recipient_kind="guardian", recipient_email="p@home.com",
        channel=channel, category="attendance", subject="Attendance alert",
        body="Your child was marked absent.", status="queued",
    )


@pytest.mark.django_db
def test_in_app_is_sent_immediately(tenant_id):
    n = deliver(_note(tenant_id, "in_app"))
    assert n.status == "sent"
    assert n.sent_at is not None


@pytest.mark.django_db
def test_external_channel_without_provider_stays_queued(tenant_id, monkeypatch):
    monkeypatch.delenv("CYED_NOTIFY_SMS_ENABLED", raising=False)
    n = deliver(_note(tenant_id, "sms"))
    assert n.status == "queued"
    assert n.sent_at is None


@pytest.mark.django_db
def test_enabled_but_unwired_provider_fails_loudly(tenant_id, monkeypatch):
    """The dangerous case: flag on, no provider. Must NOT report success."""
    monkeypatch.setenv("CYED_NOTIFY_SMS_ENABLED", "1")
    monkeypatch.delenv("CYED_NOTIFY_SMS_PROVIDER", raising=False)
    n = deliver(_note(tenant_id, "sms"))
    assert n.status == "failed", "delivery claimed success without a provider"
    assert n.sent_at is None
    # The invariant is that the reason is recorded and names the missing
    # configuration — not any particular wording, which changed when real
    # provider adapters landed.
    assert n.error
    assert "provider" in n.error.lower()


@pytest.mark.django_db
def test_wired_provider_marks_sent(tenant_id, monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_SMS_ENABLED", "1")
    monkeypatch.setattr("products.cyed.notifications.delivery._send_external", lambda n: None)
    n = deliver(_note(tenant_id, "sms"))
    assert n.status == "sent"
    assert n.sent_at is not None
