"""Celery tasks — invoice stamping + settlement payouts.

Named-task stubs wired for the queue router (`payments.*` -> "payments" queue)
are declared at the bottom; see docs/hardening/CELERY_TASKS.md for the
task contract, retry policy, and idempotency guarantees.
"""
from celery import shared_task

from .models import UnifiedBill


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def stamp_bill_task(self, bill_id: str):
    """Route paid bill to ZATCA (SA) or JoFotara (JO) integration."""
    from products.cymed.integrations.zakata.client import ZatcaClient
    from products.cymed.integrations.jofawtra.client import JoFawtraClient
    try:
        bill = UnifiedBill.objects.get(id=bill_id)
    except UnifiedBill.DoesNotExist:
        return
    # Country routing (crude: infer from insurer country of any policy or default SA)
    country = "SA"
    try:
        pol = bill.patient_profile.insurance_policies.filter(verified_at__isnull=False).first()
        if pol and pol.insurer_code in ("NSSF",):
            country = "JO"
    except Exception:
        pass

    payload = _serialise_bill_to_xml(bill)
    try:
        if country == "SA":
            r = ZatcaClient().submit_invoice(payload)
            bill.zatca_qr = r.get("qr", "")
            bill.zatca_uuid = r.get("uuid", "")
        else:
            r = JoFawtraClient().submit_invoice(payload)
            bill.jofotara_qr = r.get("qr", "")
            bill.jofotara_uuid = r.get("uuid", "")
        bill.save(update_fields=["zatca_qr", "zatca_uuid",
                                 "jofotara_qr", "jofotara_uuid", "updated_at"])
    except Exception as exc:
        raise self.retry(exc=exc)


def _serialise_bill_to_xml(bill: UnifiedBill) -> dict:
    """Produce the payload dict expected by the integration client.
    Real UBL 2.1 / ZATCA XML generation happens inside each client."""
    return {
        "bill_number": bill.bill_number,
        "issued_at": (bill.issued_at or bill.updated_at).isoformat(),
        "patient_id": str(bill.patient_profile_id),
        "subtotal": str(bill.subtotal),
        "vat": str(bill.vat),
        "total": str(bill.total),
        "line_items": [
            {
                "code": li.service_code,
                "name": li.service_name,
                "qty": str(li.quantity),
                "unit_price": str(li.unit_price),
                "amount": str(li.amount),
                "vat": str(li.vat),
            }
            for li in bill.line_items.all()
        ],
    }


# ---------------------------------------------------------------------------
# Named task stubs — wired for CELERY_TASK_ROUTES ("payments.*" -> "payments")
# See docs/hardening/CELERY_TASKS.md for the contract + rollout plan.
# ---------------------------------------------------------------------------
@shared_task(name="payments.stamp_bill_zatca")
def stamp_bill_zatca(bill_id: str) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")


@shared_task(name="payments.stamp_bill_jofotara")
def stamp_bill_jofotara(bill_id: str) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")


@shared_task(name="payments.retry_failed_settlement")
def retry_failed_settlement(txn_id: str) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")
