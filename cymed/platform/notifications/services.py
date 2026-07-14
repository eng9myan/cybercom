"""
Notification dispatch service. Tenant-scoped, multi-channel.
Channels: email, SMS, push (FCM/APNs), in-app, webhook.
"""

import logging

from django.utils import timezone

from .models import Notification, NotificationChannel, NotificationStatus, NotificationTemplate

log = logging.getLogger("cybercom.notifications")


class NotificationService:
    """Creates and dispatches notifications via configured channels."""

    @staticmethod
    def send(
        tenant_id: str,
        recipient_id: str,
        recipient_address: str,
        channel: str,
        subject: str,
        body: str,
        template: NotificationTemplate | None = None,
        scheduled_at=None,
        metadata: dict | None = None,
    ) -> Notification:
        notification = Notification.objects.create(
            tenant_id=tenant_id,
            template=template,
            channel=channel,
            recipient_id=recipient_id,
            recipient_address=recipient_address,
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING,
            scheduled_at=scheduled_at,
            metadata=metadata or {},
        )
        if not scheduled_at:
            NotificationService._dispatch(notification)
        return notification

    @staticmethod
    def send_from_template(
        tenant_id: str,
        template_name: str,
        channel: str,
        recipient_id: str,
        recipient_address: str,
        context: dict,
        lang: str = "en",
    ) -> Notification | None:
        try:
            template = NotificationTemplate.objects.get(
                tenant_id=tenant_id, name=template_name, channel=channel, is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            log.warning(
                "Template not found: %s/%s for tenant %s", template_name, channel, tenant_id
            )
            return None

        body = template.body_en if lang == "en" else template.body_ar
        subject = template.subject

        for key, val in context.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))
            subject = subject.replace(f"{{{{{key}}}}}", str(val))

        return NotificationService.send(
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            recipient_address=recipient_address,
            channel=channel,
            subject=subject,
            body=body,
            template=template,
        )

    @staticmethod
    def _dispatch(notification: Notification) -> None:
        channel = notification.channel
        try:
            if channel == NotificationChannel.EMAIL:
                NotificationService._send_email(notification)
            elif channel == NotificationChannel.SMS:
                NotificationService._send_sms(notification)
            elif channel == NotificationChannel.PUSH:
                NotificationService._send_push(notification)
            elif channel == NotificationChannel.IN_APP:
                NotificationService._deliver_in_app(notification)
            elif channel == NotificationChannel.WEBHOOK:
                NotificationService._invoke_webhook(notification)
            notification.status = NotificationStatus.SENT
            notification.sent_at = timezone.now()
            notification.save(update_fields=["status", "sent_at"])
        except Exception as exc:
            log.error("Notification dispatch failed: %s — %s", notification.id, exc)
            notification.status = NotificationStatus.FAILED
            notification.save(update_fields=["status"])

    @staticmethod
    def _send_email(notification: Notification) -> None:
        log.info("EMAIL → %s: %s", notification.recipient_address, notification.subject)

    @staticmethod
    def _send_sms(notification: Notification) -> None:
        log.info("SMS → %s: %s chars", notification.recipient_address, len(notification.body))

    @staticmethod
    def _send_push(notification: Notification) -> None:
        log.info("PUSH → token:%s title:%s", notification.recipient_address, notification.subject)

    @staticmethod
    def _deliver_in_app(notification: Notification) -> None:
        log.info("IN_APP → user:%s", notification.recipient_id)

    @staticmethod
    def _invoke_webhook(notification: Notification) -> None:
        log.info("WEBHOOK → %s", notification.recipient_address)

    @staticmethod
    def mark_delivered(notification_id: str, tenant_id: str) -> bool:
        updated = Notification.objects.filter(id=notification_id, tenant_id=tenant_id).update(
            status=NotificationStatus.DELIVERED
        )
        return updated > 0


class TemplateService:
    @staticmethod
    def create(
        tenant_id: str, name: str, channel: str, subject: str, body_en: str, body_ar: str
    ) -> NotificationTemplate:
        return NotificationTemplate.objects.create(
            tenant_id=tenant_id,
            name=name,
            channel=channel,
            subject=subject,
            body_en=body_en,
            body_ar=body_ar,
        )

    @staticmethod
    def get_active(tenant_id: str, name: str, channel: str) -> NotificationTemplate | None:
        return NotificationTemplate.objects.filter(
            tenant_id=tenant_id, name=name, channel=channel, is_active=True
        ).first()
