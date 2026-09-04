"""Signal handlers — trigger ZATCA / JoFotara stamping on payment."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UnifiedBill


@receiver(post_save, sender=UnifiedBill)
def stamp_invoice_after_payment(sender, instance: UnifiedBill, **kwargs):
    """Fire Celery task to submit invoice to ZATCA / JoFotara once paid."""
    if instance.status != "paid":
        return
    if instance.zatca_uuid or instance.jofotara_uuid:
        return
    try:
        from .tasks import stamp_bill_task
        stamp_bill_task.delay(str(instance.tenant_id), str(instance.id))
    except ImportError:
        # Celery not wired in test env; skip.
        return
