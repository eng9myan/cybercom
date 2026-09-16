"""
Notification transport seam: SMS and email providers.

Mirrors `payments/providers.py` deliberately — same shape, same guarantees —
because the failure mode is the same. A channel that reports success without
transmitting is worse than one that is switched off: the school believes a
parent was told their child is absent, and has a record saying so.

Three providers ship:

  console — writes the message to the log. For local development. Reports
            `sent`, and is honest about it: the message really did go where it
            was configured to go.
  smtp    — real email over SMTP. Works with SendGrid, Mailgun, AWS SES or a
            school's own relay; they all speak it, so one adapter covers the
            realistic options without a vendor SDK.
  twilio  — real SMS over Twilio's REST API. Chosen because it is what most
            Australian school platforms use, and its API is plain HTTPS form
            POST, so no SDK dependency is needed.

Anything else raises at send time. `UnconfiguredProvider` exists so a
deployment that sets a provider name without credentials fails on the first
message rather than silently dropping every absence alert.

**No message body is logged at error level.** A failed SMS carries a child's
name and their attendance — logging it to an aggregator is a privacy incident
in its own right.
"""

import json
import logging
import os
import smtplib
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMS_PROVIDER_ENV = "CYED_NOTIFY_SMS_PROVIDER"
EMAIL_PROVIDER_ENV = "CYED_NOTIFY_EMAIL_PROVIDER"
PUSH_PROVIDER_ENV = "CYED_NOTIFY_PUSH_PROVIDER"

# Network calls are given a hard ceiling. Guardian alerts are dispatched from a
# post-commit hook, and a provider that hangs would otherwise hold a worker for
# as long as the socket stays open.
TIMEOUT_SECONDS = 10


class NotificationProviderError(Exception):
    """Delivery failed. The message is recorded as `failed`, never as `sent`."""


class UnconfiguredProvider(NotificationProviderError):
    """A provider was named but cannot run — missing credentials, unknown name."""


@dataclass
class DeliveryReceipt:
    """
    What the provider said. `reference` is the provider's own id, kept so a
    delivery dispute can be traced back to their logs.
    """

    reference: str
    provider: str
    detail: str = ""


# ── SMS ──────────────────────────────────────────────────────────────────────
class SmsProvider:
    name = "base"

    def send(self, *, to: str, body: str) -> DeliveryReceipt:  # pragma: no cover
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    """Development transport. Logs at INFO without the body."""

    name = "console"

    def send(self, *, to: str, body: str) -> DeliveryReceipt:
        logger.info("SMS to %s (%d chars) — console provider", _mask(to), len(body))
        return DeliveryReceipt(reference=f"console:{_mask(to)}", provider=self.name)


class TwilioSmsProvider(SmsProvider):
    """
    Twilio REST. Form-encoded POST with basic auth — no SDK required.

    A 2xx means Twilio accepted the message for delivery, not that a handset
    received it. That distinction is why `sent` here means "the carrier has
    it": final delivery status arrives asynchronously on Twilio's webhook, and
    claiming more than we know is the defect this module exists to avoid.
    """

    name = "twilio"
    ENDPOINT = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"

    def __init__(self):
        self.sid = os.environ.get("CYED_TWILIO_ACCOUNT_SID", "")
        self.token = os.environ.get("CYED_TWILIO_AUTH_TOKEN", "")
        self.sender = os.environ.get("CYED_TWILIO_FROM", "")
        if not (self.sid and self.token and self.sender):
            raise UnconfiguredProvider(
                "Twilio SMS needs CYED_TWILIO_ACCOUNT_SID, CYED_TWILIO_AUTH_TOKEN "
                "and CYED_TWILIO_FROM."
            )

    def send(self, *, to: str, body: str) -> DeliveryReceipt:
        import base64

        payload = urllib.parse.urlencode(
            {"To": to, "From": self.sender, "Body": body}
        ).encode()
        credentials = base64.b64encode(f"{self.sid}:{self.token}".encode()).decode()
        request = urllib.request.Request(
            self.ENDPOINT.format(sid=urllib.parse.quote(self.sid)),
            data=payload,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            # Twilio puts a human-readable reason in the body; the status code
            # alone ("400") tells an operator nothing actionable.
            detail = _twilio_error(exc)
            raise NotificationProviderError(f"Twilio rejected the message: {detail}") from exc
        except Exception as exc:
            raise NotificationProviderError(f"Twilio unreachable: {exc}") from exc

        return DeliveryReceipt(
            reference=data.get("sid", ""),
            provider=self.name,
            detail=data.get("status", ""),
        )


def _twilio_error(exc) -> str:
    try:
        body = json.loads(exc.read().decode() or "{}")
        return body.get("message") or str(exc)
    except Exception:
        return str(exc)


# ── Email ────────────────────────────────────────────────────────────────────
class EmailProvider:
    name = "base"

    def send(self, *, to: str, subject: str, body: str) -> DeliveryReceipt:  # pragma: no cover
        raise NotImplementedError


class ConsoleEmailProvider(EmailProvider):
    name = "console"

    def send(self, *, to: str, subject: str, body: str) -> DeliveryReceipt:
        logger.info("Email to %s — %s (console provider)", _mask(to), subject)
        return DeliveryReceipt(reference=f"console:{_mask(to)}", provider=self.name)


class SmtpEmailProvider(EmailProvider):
    """
    SMTP. One adapter covers SendGrid, Mailgun, SES and a school's own relay —
    they all speak it, and a vendor SDK would buy nothing but a dependency.
    """

    name = "smtp"

    def __init__(self):
        self.host = os.environ.get("CYED_SMTP_HOST", "")
        self.port = int(os.environ.get("CYED_SMTP_PORT", "587"))
        self.user = os.environ.get("CYED_SMTP_USER", "")
        self.password = os.environ.get("CYED_SMTP_PASSWORD", "")
        self.sender = os.environ.get("CYED_SMTP_FROM", "")
        self.use_tls = os.environ.get("CYED_SMTP_TLS", "1") == "1"
        if not (self.host and self.sender):
            raise UnconfiguredProvider(
                "SMTP email needs CYED_SMTP_HOST and CYED_SMTP_FROM."
            )

    def send(self, *, to: str, subject: str, body: str) -> DeliveryReceipt:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=TIMEOUT_SECONDS) as smtp:
                if self.use_tls:
                    smtp.starttls(context=ssl.create_default_context())
                if self.user:
                    smtp.login(self.user, self.password)
                smtp.send_message(message)
        except Exception as exc:
            raise NotificationProviderError(f"SMTP delivery failed: {exc}") from exc

        return DeliveryReceipt(reference=message["Message-ID"] or "", provider=self.name)


# ── Push ─────────────────────────────────────────────────────────────────────
class PushProvider:
    name = "base"

    def send(self, *, device, subject: str, body: str) -> DeliveryReceipt:  # pragma: no cover
        raise NotImplementedError


class ConsolePushProvider(PushProvider):
    name = "console"

    def send(self, *, device, subject, body) -> DeliveryReceipt:
        logger.info("Push to %s device %s — %s", device.platform, _mask(device.token), subject)
        return DeliveryReceipt(reference=f"console:{_mask(device.token)}", provider=self.name)


class WebPushProvider(PushProvider):
    """
    Web push via an application server (VAPID).

    Requires `pywebpush`, which is an optional dependency: a school running
    without push should not have to install a crypto stack it will never call.
    The import is therefore inside `send`, and its absence is an
    `UnconfiguredProvider` rather than a startup crash.
    """

    name = "webpush"

    def __init__(self):
        self.private_key = os.environ.get("CYED_VAPID_PRIVATE_KEY", "")
        self.subject = os.environ.get("CYED_VAPID_SUBJECT", "")
        if not (self.private_key and self.subject):
            raise UnconfiguredProvider(
                "Web push needs CYED_VAPID_PRIVATE_KEY and CYED_VAPID_SUBJECT "
                "(a mailto: or https: contact for your application server)."
            )

    def send(self, *, device, subject, body) -> DeliveryReceipt:
        try:
            from pywebpush import WebPushException, webpush
        except ImportError as exc:
            raise UnconfiguredProvider(
                "Web push is configured but `pywebpush` is not installed."
            ) from exc

        if not (device.endpoint and device.p256dh and device.auth):
            raise NotificationProviderError(
                "This device is missing its web-push keys and cannot be reached."
            )

        try:
            response = webpush(
                subscription_info={
                    "endpoint": device.endpoint,
                    "keys": {"p256dh": device.p256dh, "auth": device.auth},
                },
                data=json.dumps({"title": subject, "body": body}),
                vapid_private_key=self.private_key,
                vapid_claims={"sub": self.subject},
                timeout=TIMEOUT_SECONDS,
            )
        except WebPushException as exc:
            # 404/410 mean the browser dropped the subscription. Surfaced with
            # the status so the caller can retire the device rather than
            # retrying a token that will never work again.
            status = getattr(getattr(exc, "response", None), "status_code", None)
            raise NotificationProviderError(f"Push rejected ({status}): {exc}") from exc
        except Exception as exc:
            raise NotificationProviderError(f"Push service unreachable: {exc}") from exc

        return DeliveryReceipt(
            reference=str(getattr(response, "status_code", "")), provider=self.name
        )


# Statuses that mean the subscription is gone for good, not failing transiently.
DEAD_SUBSCRIPTION_CODES = ("404", "410")


# ── selection ────────────────────────────────────────────────────────────────
SMS_PROVIDERS = {"console": ConsoleSmsProvider, "twilio": TwilioSmsProvider}
EMAIL_PROVIDERS = {"console": ConsoleEmailProvider, "smtp": SmtpEmailProvider}
PUSH_PROVIDERS = {"console": ConsolePushProvider, "webpush": WebPushProvider}

# Test seam. Set by tests to a fake transport; never consulted in production
# because nothing else assigns to it.
_OVERRIDES: dict = {}


def set_override(channel: str, provider):
    """Install a provider for one channel. Tests only; pass None to clear."""
    if provider is None:
        _OVERRIDES.pop(channel, None)
    else:
        _OVERRIDES[channel] = provider


def get_provider(channel: str):
    """
    The provider for a channel, or raise.

    Raising on an unknown name is deliberate: a typo in
    `CYED_NOTIFY_SMS_PROVIDER` must not silently degrade to console and make a
    school think its alerts are going out.
    """
    if channel in _OVERRIDES:
        return _OVERRIDES[channel]

    if channel == "sms":
        name = os.environ.get(SMS_PROVIDER_ENV, "").strip().lower()
        registry, label = SMS_PROVIDERS, "CYED_NOTIFY_SMS_PROVIDER"
    elif channel == "email":
        name = os.environ.get(EMAIL_PROVIDER_ENV, "").strip().lower()
        registry, label = EMAIL_PROVIDERS, "CYED_NOTIFY_EMAIL_PROVIDER"
    elif channel == "push":
        name = os.environ.get(PUSH_PROVIDER_ENV, "").strip().lower()
        registry, label = PUSH_PROVIDERS, "CYED_NOTIFY_PUSH_PROVIDER"
    else:
        raise UnconfiguredProvider(
            f"No provider seam exists for the '{channel}' channel yet."
        )

    if not name:
        raise UnconfiguredProvider(
            f"{label} is not set, so {channel} messages cannot be delivered."
        )
    if name not in registry:
        raise UnconfiguredProvider(
            f"{label}='{name}' is not a known provider. Available: "
            f"{', '.join(sorted(registry))}."
        )
    return registry[name]()


def _mask(value: str) -> str:
    """
    Last four characters only.

    Log lines are aggregated and retained; a full guardian phone number or
    email in them is personal information leaving the system by the back door.
    """
    value = value or ""
    return f"…{value[-4:]}" if len(value) > 4 else "…"
