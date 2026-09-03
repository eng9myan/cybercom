"""Send templated messages via cyintegrationhub SMS/Email/WhatsApp providers."""
from __future__ import annotations

import os
from string import Template

from django.utils import timezone

from .models import Campaign, CampaignSend


def render(template_body: str, context: dict) -> str:
    """Simple {{key}} substitution — replaces with dict values."""
    text = template_body
    for k, v in context.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def queue_send(*, campaign_id, patient_profile_id, channel_address: str,
                context: dict) -> CampaignSend:
    campaign = Campaign.objects.get(id=campaign_id)
    payload = render(campaign.body_template, context)
    return CampaignSend.objects.create(
        campaign=campaign, patient_profile_id=patient_profile_id,
        channel_address=channel_address, payload=payload, status="queued",
    )


def dispatch(send_id: str) -> CampaignSend:
    """Call the appropriate provider (SMS/WhatsApp/Email)."""
    send = CampaignSend.objects.get(id=send_id)
    channel = send.campaign.channel

    ok = True
    ref = ""
    err = ""
    try:
        if channel == "sms":
            ok, ref = _send_sms(send.channel_address, send.payload)
        elif channel == "whatsapp":
            ok, ref = _send_whatsapp(send.channel_address, send.payload)
        elif channel == "email":
            ok, ref = _send_email(send.channel_address, send.campaign.subject, send.payload)
        else:
            ok = False
            err = f"channel {channel} not implemented"
    except Exception as exc:  # noqa: BLE001
        ok = False
        err = str(exc)

    send.status = "sent" if ok else "failed"
    send.provider_reference = ref
    send.error_message = err
    send.sent_at = timezone.now() if ok else None
    send.save(update_fields=["status", "provider_reference", "error_message",
                              "sent_at", "updated_at"])
    return send


def _send_sms(to: str, body: str) -> tuple[bool, str]:
    """Wire to your SMS provider (Twilio, Unifonic, MessageBird). Stub returns success."""
    return True, f"sms-{to[-4:]}"


def _send_whatsapp(to: str, body: str) -> tuple[bool, str]:
    """Wire to Meta Cloud API / 360dialog. Stub returns success."""
    return True, f"wa-{to[-4:]}"


def _send_email(to: str, subject: str, html: str) -> tuple[bool, str]:
    """Wire to SES / SendGrid / Mailgun. Stub returns success."""
    return True, f"email-{to.split('@')[0]}"
