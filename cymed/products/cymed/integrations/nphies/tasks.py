"""Celery tasks for CyMed <-> NPHIES bridge.

Named-task stubs wired for the queue router (`integrations.*` -> "integrations").
See docs/hardening/CELERY_TASKS.md for the task contract, retry policy, and
idempotency guarantees.
"""
from celery import shared_task


@shared_task(name="integrations.nphies_submit_claim")
def nphies_submit_claim(claim_payload: dict) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")


@shared_task(name="integrations.nphies_check_eligibility_async")
def nphies_check_eligibility_async(payload: dict) -> str:
    raise NotImplementedError("wired but not implemented — see docs/hardening/CELERY_TASKS.md")
