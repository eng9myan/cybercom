"""
Push notifications and newsletters.

`push` used to be a channel choice with nothing behind it — a school could
enable it and believe alerts were going out. These tests cover the registration
it now needs, the multi-device fan-out, and the retirement of dead
subscriptions. Newsletters are tested mostly for the two ways bulk mail goes
wrong: sending twice, and sending to the wrong people.
"""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.hr.models import Staff
from products.cyed.notifications import newsletters, providers
from products.cyed.notifications.delivery import deliver
from products.cyed.notifications.models import Newsletter, Notification, PushDevice
from products.cyed.notifications.providers import NotificationProviderError
from products.cyed.sis.models import Guardian, Student

pytestmark = pytest.mark.django_db


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def office(client_for):
    return client_for(["tenant_admin"], "office@cyed.edu.au")


@pytest.fixture
def parent(client_for):
    return client_for(["parent"], "hoa@example.com")


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    for channel in ("sms", "email", "push"):
        providers.set_override(channel, None)


class RecordingPush(providers.PushProvider):
    name = "recording"

    def __init__(self):
        self.sent = []

    def send(self, *, device, subject, body):
        self.sent.append((device.token, subject))
        return providers.DeliveryReceipt(reference="push-1", provider=self.name)


class DeadSubscriptionPush(providers.PushProvider):
    name = "dead"

    def send(self, *, device, subject, body):
        raise NotificationProviderError("Push rejected (410): subscription gone")


def _device(tenant_id, email="hoa@example.com", token="tok-1"):
    return PushDevice.objects.create(
        tenant_id=tenant_id, owner_email=email, platform="web", token=token,
        endpoint=f"https://push.example/{token}", p256dh="key", auth="auth",
    )


def _note(tenant_id, **extra):
    body = {
        "tenant_id": tenant_id,
        "recipient_kind": "guardian",
        "recipient_name": "Hoa Tran",
        "recipient_email": "hoa@example.com",
        "channel": "push",
        "category": "attendance",
        "subject": "Attendance alert",
        "body": "Mia was marked absent.",
        "status": "queued",
    }
    body.update(extra)
    return Notification.objects.create(**body)


# ── registration ─────────────────────────────────────────────────────────────
def test_a_device_registers_against_the_authenticated_account(parent, tenant_id):
    """
    Registering against an email from the body would let anyone subscribe to
    someone else's notifications.
    """
    resp = parent.post("/api/v1/notifications/devices/", {
        "platform": "web", "token": "tok-abc",
        "endpoint": "https://push.example/abc", "p256dh": "k", "auth": "a",
        "owner_email": "someone.else@example.com",
    }, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["owner_email"] == "hoa@example.com"


def test_a_web_registration_without_keys_is_refused(parent):
    """Without all three the browser is unreachable and the device looks fine."""
    resp = parent.post("/api/v1/notifications/devices/", {
        "platform": "web", "token": "tok-nokeys",
    }, format="json")
    assert resp.status_code == 400
    assert "endpoint, p256dh and auth" in str(resp.data)


def test_re_registering_the_same_token_reactivates_it(parent, tenant_id):
    """A revoked-then-regranted browser sends the same subscription back."""
    body = {
        "platform": "web", "token": "tok-same",
        "endpoint": "https://push.example/same", "p256dh": "k", "auth": "a",
    }
    parent.post("/api/v1/notifications/devices/", body, format="json")
    PushDevice.objects.filter(token="tok-same").update(is_active=False)

    parent.post("/api/v1/notifications/devices/", body, format="json")
    assert PushDevice.objects.filter(tenant_id=tenant_id, token="tok-same").count() == 1
    assert PushDevice.objects.get(token="tok-same").is_active is True


def test_people_see_only_their_own_devices(parent, office, tenant_id):
    """A token is a credential; a list of everyone's is a map of who uses what."""
    _device(tenant_id, "hoa@example.com", "tok-parent")
    _device(tenant_id, "office@cyed.edu.au", "tok-office")

    rows = parent.get("/api/v1/notifications/devices/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert [r["token"] for r in rows] == ["tok-parent"]


# ── delivery ─────────────────────────────────────────────────────────────────
def test_push_reaches_every_registered_device(tenant_id, monkeypatch):
    """A person with a phone and a laptop should have both buzz."""
    monkeypatch.setenv("CYED_NOTIFY_PUSH_ENABLED", "1")
    transport = RecordingPush()
    providers.set_override("push", transport)
    _device(tenant_id, token="tok-phone")
    _device(tenant_id, token="tok-laptop")

    note = deliver(_note(tenant_id))

    assert note.status == "sent"
    assert {t for t, _ in transport.sent} == {"tok-phone", "tok-laptop"}


def test_a_recipient_with_no_device_fails_honestly(tenant_id, monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_PUSH_ENABLED", "1")
    providers.set_override("push", RecordingPush())

    note = deliver(_note(tenant_id))
    assert note.status == "failed"
    assert "no registered device" in note.error


def test_a_dead_subscription_is_retired_not_retried_forever(tenant_id, monkeypatch):
    """
    A browser that dropped the subscription returns 410 forever; retrying it
    fills the queue with work that can never succeed.
    """
    monkeypatch.setenv("CYED_NOTIFY_PUSH_ENABLED", "1")
    providers.set_override("push", DeadSubscriptionPush())
    device = _device(tenant_id, token="tok-dead")

    note = deliver(_note(tenant_id))

    assert note.status == "failed"
    device.refresh_from_db()
    assert device.is_active is False
    assert "410" in device.failure_reason


def test_one_working_device_is_enough(tenant_id, monkeypatch):
    """
    Requiring every device to succeed would mark a delivered message failed
    because an old laptop's subscription expired.
    """
    monkeypatch.setenv("CYED_NOTIFY_PUSH_ENABLED", "1")

    class Flaky(providers.PushProvider):
        name = "flaky"

        def send(self, *, device, subject, body):
            if device.token == "tok-dead":
                raise NotificationProviderError("Push rejected (410): gone")
            return providers.DeliveryReceipt(reference="ok", provider=self.name)

    providers.set_override("push", Flaky())
    _device(tenant_id, token="tok-dead")
    _device(tenant_id, token="tok-live")

    assert deliver(_note(tenant_id)).status == "sent"


def test_push_without_a_provider_configured_fails_loudly(tenant_id, monkeypatch):
    monkeypatch.setenv("CYED_NOTIFY_PUSH_ENABLED", "1")
    monkeypatch.delenv("CYED_NOTIFY_PUSH_PROVIDER", raising=False)
    _device(tenant_id)

    note = deliver(_note(tenant_id))
    assert note.status == "failed"
    assert "is not set" in note.error


# ── newsletters ──────────────────────────────────────────────────────────────
@pytest.fixture
def school(tenant_id):
    students, guardians = [], []
    for i, year in enumerate([8, 9, 9, 12]):
        s = Student.objects.create(
            tenant_id=tenant_id, first_name=f"S{i}", last_name="Test",
            year_level=year, enrolment_status="enrolled", email=f"s{i}@student.cyed.edu.au",
        )
        g = Guardian.objects.create(
            tenant_id=tenant_id, first_name=f"G{i}", last_name="Test",
            email=f"g{i}@example.com",
        )
        g.students.add(s)
        students.append(s)
        guardians.append(g)
    Staff.objects.create(
        tenant_id=tenant_id, first_name="Ada", last_name="Staff", email="ada@cyed.edu.au"
    )
    return students, guardians


def _newsletter(tenant_id, **extra):
    body = {
        "tenant_id": tenant_id,
        "title": "Week 4 newsletter",
        "body": "Assembly on Friday.",
        "audience": "parents",
        "channel": "in_app",
    }
    body.update(extra)
    return Newsletter.objects.create(**body)


def test_preview_counts_before_anyone_presses_send(office, tenant_id, school):
    """"All parents" and "Year 9 parents" differ by nine hundred recipients."""
    news = _newsletter(tenant_id)
    resp = office.get(f"/api/v1/notifications/newsletters/{news.id}/preview/")
    assert resp.data["total"] == 4
    assert resp.data["by_kind"]["guardian"] == 4


def test_year_targeting_reaches_the_right_families(tenant_id, school):
    news = _newsletter(tenant_id, year_levels="9")
    assert newsletters.preview(news)["total"] == 2


def test_a_guardian_with_two_children_gets_one_copy(tenant_id, school):
    """The commonest complaint about school bulk mail."""
    students, guardians = school
    guardians[0].students.add(students[1])

    news = _newsletter(tenant_id)
    assert newsletters.preview(news)["total"] == 4


def test_sending_fans_out_into_ordinary_notifications(office, tenant_id, school):
    """Reusing the delivery path is what makes the report honest."""
    news = _newsletter(tenant_id)
    resp = office.post(f"/api/v1/notifications/newsletters/{news.id}/send/", {}, format="json")

    assert resp.status_code == 200
    assert resp.data["recipients"] == 4
    assert Notification.objects.filter(
        tenant_id=tenant_id, category="announcement"
    ).count() == 4


def test_a_newsletter_cannot_be_sent_twice(office, tenant_id, school):
    """A school that mails every family twice spends the next hour apologising."""
    news = _newsletter(tenant_id)
    office.post(f"/api/v1/notifications/newsletters/{news.id}/send/", {}, format="json")
    again = office.post(f"/api/v1/notifications/newsletters/{news.id}/send/", {}, format="json")

    assert again.status_code == 409
    assert "already sent" in again.data["detail"]
    assert Notification.objects.filter(tenant_id=tenant_id, category="announcement").count() == 4


def test_an_audience_matching_nobody_is_refused(office, tenant_id, school):
    news = _newsletter(tenant_id, year_levels="11")
    resp = office.post(f"/api/v1/notifications/newsletters/{news.id}/send/", {}, format="json")
    assert resp.status_code == 409
    assert "matches nobody" in resp.data["detail"]


def test_sms_is_not_offered_for_bulk(office, tenant_id, school):
    """A weekly newsletter to 900 families over SMS is a bill nobody approved."""
    news = _newsletter(tenant_id, channel="sms")
    resp = office.post(f"/api/v1/notifications/newsletters/{news.id}/send/", {}, format="json")
    assert resp.status_code == 409
    assert "cannot be used for a bulk send" in resp.data["detail"]


def test_staff_audience_reaches_staff(tenant_id, school):
    news = _newsletter(tenant_id, audience="staff")
    assert newsletters.preview(news)["by_kind"] == {"staff": 1}


def test_the_delivery_report_counts_real_outcomes(office, tenant_id, school):
    news = _newsletter(tenant_id)
    office.post(f"/api/v1/notifications/newsletters/{news.id}/send/", {}, format="json")

    resp = office.get(f"/api/v1/notifications/newsletters/{news.id}/delivery-report/")
    assert resp.data["by_status"]["sent"] == 4
    assert resp.data["failures"] == []


def test_families_cannot_send_newsletters(parent, tenant_id):
    news = _newsletter(tenant_id)
    assert parent.post(
        f"/api/v1/notifications/newsletters/{news.id}/send/", {}, format="json"
    ).status_code == 403


def test_a_bad_year_level_is_refused(office):
    resp = office.post("/api/v1/notifications/newsletters/", {
        "title": "Typo", "body": "x", "year_levels": "nine",
    }, format="json")
    assert resp.status_code == 400
