from django.db.models.signals import post_save
from django.dispatch import receiver


def _publish(tenant_id, event_type, payload):
    try:
        from platform.events.outbox import OutboxEvent
        OutboxEvent.publish(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _push_to_cycom(tenant_id, event_type, payload):
    """Route financial data to CyCom Finance via CyIntegrationHub — no shared ORM."""
    try:
        from platform.integrations.hub import CyIntegrationHub
        CyIntegrationHub.send(
            tenant_id=tenant_id,
            destination="cycom_finance",
            event_type=event_type,
            payload=payload,
        )
    except Exception:
        pass


@receiver(post_save, sender="cymed_rcm_claims.Claim")
def on_claim_submitted(sender, instance, created, **kwargs):
    if not created and instance.status == "submitted":
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.rcm.claim.submitted",
            payload={"claim_id": str(instance.id), "claim_number": instance.claim_number},
        )


@receiver(post_save, sender="cymed_rcm_billing.Invoice")
def on_invoice_approved(sender, instance, created, **kwargs):
    if not created and instance.status == "approved":
        _push_to_cycom(
            tenant_id=instance.tenant_id,
            event_type="cymed.rcm.invoice.approved",
            payload={
                "invoice_id": str(instance.id),
                "invoice_number": instance.invoice_number,
                "amount_total": str(instance.amount_total),
                "patient_account_id": str(instance.patient_account_id),
            },
        )


@receiver(post_save, sender="cymed_rcm_collections.CollectionCase")
def on_collection_case_created(sender, instance, created, **kwargs):
    if created:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.rcm.collection_case.created",
            payload={
                "case_id": str(instance.id),
                "patient_id": str(instance.patient_id),
                "outstanding_balance": str(instance.outstanding_balance),
            },
        )
