from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.marketing.models import Campaign
from products.cycom.marketing.sms import get_sms_backend


def add_recipients(campaign: Campaign, contacts: list[str]) -> int:
    from products.cycom.marketing.models import MarketingRecipient

    created = 0
    for contact in contacts:
        contact = contact.strip()
        if not contact:
            continue
        _, was_created = MarketingRecipient.objects.get_or_create(
            tenant_id=campaign.tenant_id, campaign=campaign, contact=contact
        )
        created += int(was_created)
    return created


@transaction.atomic
def send_campaign(campaign: Campaign) -> Campaign:
    """
    Real delivery: django.core.mail.send_mail for email/newsletter (backed
    by whatever EMAIL_BACKEND is configured — SMTP in prod, console in
    dev/test, same as any other Django app's outbound mail), and the
    pluggable SMS backend for sms campaigns. Each recipient is attempted
    independently — one failure doesn't block the rest.
    """
    if campaign.state not in ("draft", "in_queue"):
        raise ValidationError(f"Campaign is '{campaign.state}', cannot send.")
    pending = list(campaign.recipients.filter(status="pending"))
    if not pending:
        raise ValidationError("Campaign has no pending recipients.")

    campaign.state = "sending"
    campaign.save(update_fields=["state", "updated_at"])

    sent = failed = 0
    sms_backend = get_sms_backend() if campaign.campaign_type == "sms" else None

    for recipient in pending:
        try:
            if campaign.campaign_type == "sms":
                ok = sms_backend.send(to=recipient.contact, body=campaign.body)
                if not ok:
                    raise RuntimeError("SMS backend reported failure.")
            else:
                send_mail(
                    subject=campaign.name,
                    message=campaign.body,
                    from_email=None,
                    recipient_list=[recipient.contact],
                    fail_silently=False,
                )
            recipient.status = "sent"
            recipient.sent_at = timezone.now()
            recipient.save(update_fields=["status", "sent_at", "updated_at"])
            sent += 1
        except Exception as exc:  # noqa: BLE001 — one bad recipient must not abort the send
            recipient.status = "failed"
            recipient.error_message = str(exc)
            recipient.save(update_fields=["status", "error_message", "updated_at"])
            failed += 1

    campaign.sent += sent
    campaign.failed += failed
    campaign.state = "done"
    campaign.save(update_fields=["sent", "failed", "state", "updated_at"])
    return campaign
