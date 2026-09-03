"""Celery tasks for outbound notifications (SMS / WhatsApp / Email).

Named-task stubs wired for the queue router (`notifications.*` -> "notifications").
See docs/hardening/CELERY_TASKS.md for the task contract, retry policy, and
idempotency guarantees.
"""
from celery import shared_task


@shared_task(name="notifications.send_sms")
def send_sms(to: str, body: str) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")


@shared_task(name="notifications.send_whatsapp")
def send_whatsapp(to: str, body: str) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")


@shared_task(name="notifications.send_email")
def send_email(to: str, subject: str, html: str) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")
