"""
Audit & Compliance Celery tasks.
"""

import logging

from celery import shared_task
from django.utils import timezone

log = logging.getLogger(__name__)


@shared_task(name="audit.verify_chains")
def verify_chains_task():
    """Verify all audit hash chains for tampering. ADR-0028 S5.1."""
    from .services import AuditChainVerifier

    results = AuditChainVerifier().verify_all()
    invalid = [r for r in results if not r.get("valid")]
    if invalid:
        log.error("AUDIT CHAIN INTEGRITY FAILURE: %s chains invalid: %s", len(invalid), invalid)
    else:
        log.info("Audit chain verification: all %s chains valid", len(results))
    return {"total": len(results), "invalid": len(invalid)}


@shared_task(name="audit.archive_expired")
def archive_expired_events_task():
    """Move events past hot retention into archive records."""
    from django.db.models import Count, Max, Min

    from .models import (
        AuditArchive,
        AuditCategoryCode,
        AuditEvent,
        AuditRetentionPolicy,
    )

    archived = 0
    for category in AuditCategoryCode.values:
        policy = AuditRetentionPolicy.objects.filter(
            tenant_id=None, category=category, is_active=True
        ).first()
        if not policy:
            continue
        cutoff = timezone.now() - timezone.timedelta(days=policy.hot_retention_days)
        old_events = AuditEvent.objects.filter(category=category, timestamp__lt=cutoff)
        if not old_events.exists():
            continue
        agg = old_events.aggregate(
            count=Count("id"), min_ts=Min("timestamp"), max_ts=Max("timestamp")
        )
        archive_key = f"global/{category}/{agg['min_ts'].date()}-{agg['max_ts'].date()}"
        if not AuditArchive.objects.filter(archive_key=archive_key).exists():
            AuditArchive.objects.create(
                archive_key=archive_key,
                category=category,
                period_start=agg["min_ts"],
                period_end=agg["max_ts"],
                event_count=agg["count"],
            )
            archived += agg["count"]
    log.info("Archive sweep: %s events marked for archival", archived)
    return {"archived": archived}


@shared_task(name="audit.expire_legal_holds")
def expire_legal_holds_task():
    """Mark expired legal holds as LegalHoldStatus.EXPIRED."""
    from .models import LegalHold, LegalHoldStatus

    now = timezone.now()
    expired = LegalHold.objects.filter(
        status=LegalHoldStatus.ACTIVE,
        expires_at__lt=now,
    )
    count = expired.count()
    expired.update(status=LegalHoldStatus.EXPIRED)
    log.info("Expired %s legal holds", count)
    return {"expired": count}


@shared_task(name="audit.run_compliance_assessments")
def run_compliance_assessments_task():
    """Run automated compliance assessment for all active profiles."""
    from .models import ComplianceProfile
    from .services import ComplianceAssessmentService

    svc = ComplianceAssessmentService()
    profiles = ComplianceProfile.objects.filter(is_active=True)
    results = []
    for profile in profiles:
        try:
            assessment = svc.assess(profile, tenant_id=profile.tenant_id)
            results.append(
                {"profile": str(profile.id), "score": assessment.score, "result": assessment.result}
            )
        except Exception:
            log.exception("Assessment failed for profile %s", profile.id)
    log.info("Compliance assessments: %s profiles assessed", len(results))
    return {"assessed": len(results), "results": results}


@shared_task(name="audit.expire_exports")
def expire_exports_task():
    """Mark AuditExport records past their expiry as expired."""
    from .models import AuditExport

    now = timezone.now()
    expired = AuditExport.objects.filter(status="ready", expires_at__lt=now)
    count = expired.count()
    expired.update(status="expired")
    log.info("Expired %s audit export records", count)
    return {"expired": count}
