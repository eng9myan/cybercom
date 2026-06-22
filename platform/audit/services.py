"""
Audit & Compliance service layer. ADR-0028.
"""
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    AuditAction, AuditCategoryCode, AuditChain, AuditEvent, AuditEntry,
    AuditExport, AuditLog, AuditRetentionPolicy, AuditArchive, AuditSignature,
    AuditStatus, AssessmentResult, ComplianceAssessment, ComplianceFrameworkCode,
    ComplianceProfile, ComplianceReport, ComplianceRule, ComplianceRuleSeverity,
    ComplianceViolation, DataClassification, EvidencePackage, EvidenceRecord,
    LegalHold, LegalHoldStatus, ViolationStatus,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AuditService — write canonical audit events
# ---------------------------------------------------------------------------

class AuditService:
    """
    Central audit writer. All bounded contexts call this to emit audit events.
    Maintains hash chain per tenant. ADR-0028 S5.
    """

    def record(
        self,
        action: str,
        action_verb: str,
        resource_type: str,
        resource_id: str = "",
        tenant_id=None,
        tenant_slug: str = "",
        actor_user_id: str = "",
        actor_username: str = "",
        actor_role_claims: list = None,
        actor_ip: str = None,
        actor_device_id: str = "",
        actor_session_id: str = "",
        category: str = AuditCategoryCode.SYSTEM,
        data_classification: str = DataClassification.INTERNAL,
        purpose_of_use: str = "",
        correlation_id: str = "",
        trace_id: str = "",
        status: str = AuditStatus.SUCCESS,
        outcome_description: str = "",
        error_code: str = "",
        before_state=None,
        after_state=None,
        payload: dict = None,
    ) -> AuditEvent:
        chain_key = self._chain_key(tenant_id)
        with transaction.atomic():
            chain, _ = AuditChain.objects.select_for_update().get_or_create(
                chain_key=chain_key,
                defaults={"tenant_id": tenant_id},
            )
            event = AuditEvent(
                tenant_id=tenant_id,
                tenant_slug=tenant_slug,
                actor_user_id=actor_user_id,
                actor_username=actor_username,
                actor_role_claims=actor_role_claims or [],
                actor_ip=actor_ip,
                actor_device_id=actor_device_id,
                actor_session_id=actor_session_id,
                action=action,
                action_verb=action_verb,
                category=category,
                data_classification=data_classification,
                resource_type=resource_type,
                resource_id=resource_id,
                purpose_of_use=purpose_of_use,
                correlation_id=correlation_id,
                trace_id=trace_id,
                status=status,
                outcome_description=outcome_description,
                error_code=error_code,
                before_state=before_state,
                after_state=after_state,
                payload=payload or {},
                previous_hash=chain.last_hash,
                chain_sequence=chain.current_sequence + 1,
            )
            event.entry_hash = event.compute_hash()
            event.save()

            chain.current_sequence += 1
            chain.last_hash = event.entry_hash
            chain.last_event_id = event.id
            chain.total_events += 1
            chain.save(update_fields=["current_sequence", "last_hash", "last_event_id", "total_events", "last_updated"])

            AuditEntry.objects.create(
                event=event,
                chain=chain,
                sequence=event.chain_sequence,
                compliance_tags=self._compliance_tags(category, data_classification),
                is_high_risk=self._is_high_risk(action_verb, category, data_classification),
                risk_score=self._risk_score(action_verb, category, data_classification),
            )
        return event

    def _chain_key(self, tenant_id) -> str:
        return f"tenant:{tenant_id}" if tenant_id else "platform:global"

    def _compliance_tags(self, category: str, classification: str) -> list:
        tags = []
        if category == AuditCategoryCode.CLINICAL or classification == DataClassification.PHI:
            tags.append("hipaa")
        if classification in (DataClassification.PII, DataClassification.PHI):
            tags.extend(["gdpr", "pdpl"])
        if category == AuditCategoryCode.FINANCIAL:
            tags.extend(["pci_dss", "soc2"])
        if category == AuditCategoryCode.GOVERNMENT:
            tags.append("nca_ecc")
        return tags

    def _is_high_risk(self, verb: str, category: str, classification: str) -> bool:
        high_risk_verbs = {AuditAction.BREAK_GLASS, AuditAction.DELETE, AuditAction.PURGE, AuditAction.EXPORT}
        high_risk_classes = {DataClassification.PHI, DataClassification.RESTRICTED, DataClassification.GOVERNMENT_SENSITIVE}
        return verb in high_risk_verbs or classification in high_risk_classes

    def _risk_score(self, verb: str, category: str, classification: str) -> int:
        score = 0
        verb_scores = {
            AuditAction.BREAK_GLASS: 100, AuditAction.PURGE: 90, AuditAction.DELETE: 70,
            AuditAction.EXPORT: 60, AuditAction.UPDATE: 40, AuditAction.CREATE: 20,
            AuditAction.READ: 10,
        }
        class_scores = {
            DataClassification.PHI: 50, DataClassification.RESTRICTED: 40,
            DataClassification.GOVERNMENT_SENSITIVE: 40, DataClassification.PII: 30,
            DataClassification.FINANCIAL: 30, DataClassification.CONFIDENTIAL: 20,
        }
        score += verb_scores.get(verb, 10)
        score += class_scores.get(classification, 0)
        return min(score, 100)


# ---------------------------------------------------------------------------
# AuditChainVerifier — tamper detection
# ---------------------------------------------------------------------------

class AuditChainVerifier:
    """Verifies hash chain integrity for a given chain key."""

    def verify(self, chain_key: str) -> dict:
        try:
            chain = AuditChain.objects.get(chain_key=chain_key)
        except AuditChain.DoesNotExist:
            return {"valid": False, "error": "chain_not_found", "chain_key": chain_key}

        entries = AuditEntry.objects.filter(chain=chain).order_by("sequence").select_related("event")
        if not entries.exists():
            return {"valid": True, "chain_key": chain_key, "checked": 0}

        prev_hash = ""
        errors = []
        for entry in entries:
            event = entry.event
            expected = AuditEvent(
                id=event.id, timestamp=event.timestamp, action=event.action,
                resource_type=event.resource_type, resource_id=event.resource_id,
                actor_user_id=event.actor_user_id, tenant_id=event.tenant_id,
                previous_hash=prev_hash,
            ).compute_hash()
            if event.entry_hash != expected:
                errors.append({"sequence": entry.sequence, "event_id": str(event.id)})
            prev_hash = event.entry_hash

        valid = len(errors) == 0
        chain.is_verified = valid
        chain.verification_error = str(errors) if errors else ""
        chain.last_verified_at = timezone.now()
        chain.save(update_fields=["is_verified", "verification_error", "last_verified_at"])

        return {"valid": valid, "chain_key": chain_key, "checked": entries.count(), "errors": errors}

    def verify_all(self) -> list:
        results = []
        for chain in AuditChain.objects.all():
            results.append(self.verify(chain.chain_key))
        return results


# ---------------------------------------------------------------------------
# AuditSearchService
# ---------------------------------------------------------------------------

class AuditSearchService:
    """Filtered search over AuditEvent records."""

    def search(
        self,
        tenant_id=None,
        category: str = None,
        action: str = None,
        actor_user_id: str = None,
        resource_type: str = None,
        resource_id: str = None,
        status: str = None,
        data_classification: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        is_high_risk: bool = None,
        limit: int = 100,
        offset: int = 0,
    ):
        qs = AuditEvent.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if category:
            qs = qs.filter(category=category)
        if action:
            qs = qs.filter(action__icontains=action)
        if actor_user_id:
            qs = qs.filter(actor_user_id=actor_user_id)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if resource_id:
            qs = qs.filter(resource_id=resource_id)
        if status:
            qs = qs.filter(status=status)
        if data_classification:
            qs = qs.filter(data_classification=data_classification)
        if date_from:
            qs = qs.filter(timestamp__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__lte=date_to)
        if is_high_risk is not None:
            qs = qs.filter(entry__is_high_risk=is_high_risk)
        return qs.order_by("-timestamp")[offset: offset + limit]


# ---------------------------------------------------------------------------
# AuditExportService
# ---------------------------------------------------------------------------

class AuditExportService:
    """Creates and manages audit export jobs."""

    def create_export(
        self, tenant_id, requested_by: str, reason: str,
        filter_criteria: dict = None, format: str = "json",
        period_start: datetime = None, period_end: datetime = None,
    ) -> AuditExport:
        export = AuditExport.objects.create(
            tenant_id=tenant_id,
            requested_by=requested_by,
            reason=reason,
            filter_criteria=filter_criteria or {},
            format=format,
            period_start=period_start,
            period_end=period_end,
            expires_at=timezone.now() + timedelta(days=7),
        )
        return export

    def complete_export(self, export: AuditExport, event_count: int, download_url: str = "") -> None:
        export.status = "ready"
        export.event_count = event_count
        export.download_url = download_url
        export.completed_at = timezone.now()
        export.save(update_fields=["status", "event_count", "download_url", "completed_at"])

    def fail_export(self, export: AuditExport, error: str) -> None:
        export.status = "failed"
        export.error_message = error
        export.save(update_fields=["status", "error_message"])


# ---------------------------------------------------------------------------
# LegalHoldService
# ---------------------------------------------------------------------------

class LegalHoldService:
    """Create, manage, and release legal holds."""

    def create(
        self, tenant_id, name: str, description: str, created_by: str,
        case_reference: str = "", resource_types: list = None,
        resource_ids: list = None, custodians: list = None,
        expires_at: datetime = None,
    ) -> LegalHold:
        hold = LegalHold.objects.create(
            tenant_id=tenant_id,
            name=name,
            description=description,
            created_by=created_by,
            case_reference=case_reference,
            resource_types=resource_types or [],
            resource_ids=resource_ids or [],
            custodians=custodians or [],
            expires_at=expires_at,
        )
        AuditLog.objects.create(
            tenant_id=tenant_id,
            action=AuditAction.CREATE,
            resource_type="legal_hold",
            resource_id=str(hold.id),
            user_id=created_by,
            description=f"Legal hold created: {name}",
            metadata={"case_reference": case_reference},
        )
        return hold

    def release(self, hold: LegalHold, released_by: str, reason: str) -> None:
        hold.release(released_by=released_by, reason=reason)
        AuditLog.objects.create(
            tenant_id=hold.tenant_id,
            action=AuditAction.UPDATE,
            resource_type="legal_hold",
            resource_id=str(hold.id),
            user_id=released_by,
            description=f"Legal hold released: {hold.name}",
            metadata={"reason": reason},
        )

    def is_resource_held(self, tenant_id, resource_type: str, resource_id: str = None) -> bool:
        holds = LegalHold.objects.filter(tenant_id=tenant_id, status=LegalHoldStatus.ACTIVE)
        for hold in holds:
            type_match = not hold.resource_types or resource_type in hold.resource_types
            if not type_match:
                continue
            if resource_id:
                id_match = not hold.resource_ids or resource_id in hold.resource_ids
                if not id_match:
                    continue
            return True
        return False


# ---------------------------------------------------------------------------
# ComplianceProfileService
# ---------------------------------------------------------------------------

class ComplianceProfileService:
    """Manage compliance profiles and seed rules for known frameworks."""

    FRAMEWORK_RULES = {
        ComplianceFrameworkCode.HIPAA: [
            ("HIPAA-AC-1", "Unique User Identification", ComplianceRuleSeverity.CRITICAL, "authentication"),
            ("HIPAA-AC-2", "Emergency Access Procedure (Break Glass)", ComplianceRuleSeverity.CRITICAL, "clinical"),
            ("HIPAA-AU-1", "Audit Controls — Activity Logs", ComplianceRuleSeverity.CRITICAL, "security"),
            ("HIPAA-AU-2", "Audit Review and Reporting", ComplianceRuleSeverity.HIGH, "security"),
            ("HIPAA-TM-1", "Transmission Security — TLS", ComplianceRuleSeverity.CRITICAL, "security"),
            ("HIPAA-PHI-1", "PHI Isolation via RLS or T-DB", ComplianceRuleSeverity.CRITICAL, "clinical"),
            ("HIPAA-MFA-1", "MFA for Workforce Members", ComplianceRuleSeverity.HIGH, "authentication"),
        ],
        ComplianceFrameworkCode.GDPR: [
            ("GDPR-LB-1", "Lawful Basis Documented", ComplianceRuleSeverity.CRITICAL, "administrative"),
            ("GDPR-DSR-1", "Data Subject Rights Mechanism", ComplianceRuleSeverity.HIGH, "administrative"),
            ("GDPR-DM-1", "Data Minimization Controls", ComplianceRuleSeverity.MEDIUM, "configuration"),
            ("GDPR-BR-1", "Breach Notification < 72h", ComplianceRuleSeverity.CRITICAL, "security"),
            ("GDPR-DR-1", "Data Residency Enforced", ComplianceRuleSeverity.HIGH, "configuration"),
            ("GDPR-RT-1", "Retention Policy Active", ComplianceRuleSeverity.HIGH, "configuration"),
        ],
        ComplianceFrameworkCode.SOC2: [
            ("SOC2-CC1-1", "Security Policies Documented", ComplianceRuleSeverity.HIGH, "administrative"),
            ("SOC2-CC6-1", "Logical Access Controls", ComplianceRuleSeverity.CRITICAL, "authorization"),
            ("SOC2-CC7-1", "Continuous Monitoring", ComplianceRuleSeverity.HIGH, "security"),
            ("SOC2-CC8-1", "Change Management Process", ComplianceRuleSeverity.MEDIUM, "configuration"),
            ("SOC2-A1-1", "System Availability SLO", ComplianceRuleSeverity.HIGH, "system"),
        ],
        ComplianceFrameworkCode.ISO27001: [
            ("ISO-A5-1", "Information Security Policies", ComplianceRuleSeverity.HIGH, "administrative"),
            ("ISO-A9-1", "Access Control Policy", ComplianceRuleSeverity.CRITICAL, "authorization"),
            ("ISO-A12-1", "Operational Procedures Documented", ComplianceRuleSeverity.MEDIUM, "administrative"),
            ("ISO-A16-1", "Incident Management Process", ComplianceRuleSeverity.HIGH, "security"),
            ("ISO-A18-1", "Compliance Review", ComplianceRuleSeverity.MEDIUM, "administrative"),
        ],
        ComplianceFrameworkCode.NCA_ECC: [
            ("NCA-1-1", "Asset Management", ComplianceRuleSeverity.HIGH, "administrative"),
            ("NCA-2-1", "Access Control — Privileged Accounts", ComplianceRuleSeverity.CRITICAL, "authorization"),
            ("NCA-3-1", "Security Event Logging", ComplianceRuleSeverity.CRITICAL, "security"),
            ("NCA-4-1", "Data Classification", ComplianceRuleSeverity.HIGH, "configuration"),
            ("NCA-5-1", "Incident Response Plan", ComplianceRuleSeverity.HIGH, "security"),
        ],
    }

    def create_profile(
        self, framework: str, tenant_id=None, name: str = "", seed_rules: bool = True
    ) -> ComplianceProfile:
        profile = ComplianceProfile.objects.create(
            tenant_id=tenant_id,
            framework=framework,
            name=name or f"{framework.upper()} Compliance Profile",
        )
        if seed_rules and framework in self.FRAMEWORK_RULES:
            self._seed_rules(profile)
        return profile

    def _seed_rules(self, profile: ComplianceProfile) -> None:
        rules = self.FRAMEWORK_RULES.get(profile.framework, [])
        ComplianceRule.objects.bulk_create([
            ComplianceRule(
                profile=profile,
                rule_id=rule_id,
                name=name,
                description=name,
                severity=severity,
                category=category,
            )
            for rule_id, name, severity, category in rules
        ])

    def get_or_create(self, framework: str, tenant_id=None) -> ComplianceProfile:
        profile, created = ComplianceProfile.objects.get_or_create(
            tenant_id=tenant_id,
            framework=framework,
            defaults={"name": f"{framework.upper()} Profile"},
        )
        if created:
            self._seed_rules(profile)
        return profile


# ---------------------------------------------------------------------------
# ComplianceAssessmentService
# ---------------------------------------------------------------------------

class ComplianceAssessmentService:
    """Run automated compliance assessment for a profile."""

    def assess(self, profile: ComplianceProfile, tenant_id=None, assessed_by: str = "system") -> ComplianceAssessment:
        rules = list(profile.rules.filter(is_active=True))
        total = len(rules)
        passed = 0
        failed = 0
        critical_v = 0
        high_v = 0
        rule_results = {}

        open_violations = ComplianceViolation.objects.filter(
            rule__profile=profile,
            tenant_id=tenant_id,
            status__in=[ViolationStatus.OPEN, ViolationStatus.ACKNOWLEDGED],
        )
        violated_rules = set(open_violations.values_list("rule_id", flat=True))

        for rule in rules:
            is_violated = rule.id in violated_rules
            if is_violated:
                failed += 1
                if rule.severity == ComplianceRuleSeverity.CRITICAL:
                    critical_v += 1
                elif rule.severity == ComplianceRuleSeverity.HIGH:
                    high_v += 1
                rule_results[rule.rule_id] = "failed"
            else:
                passed += 1
                rule_results[rule.rule_id] = "passed"

        score = int((passed / total) * 100) if total > 0 else 100
        if critical_v > 0:
            result = AssessmentResult.FAILED
        elif score >= profile.passing_score:
            result = AssessmentResult.PASSED
        else:
            result = AssessmentResult.PARTIAL

        return ComplianceAssessment.objects.create(
            profile=profile,
            tenant_id=tenant_id,
            assessed_by=assessed_by,
            result=result,
            total_rules=total,
            passed_rules=passed,
            failed_rules=failed,
            score=score,
            critical_violations=critical_v,
            high_violations=high_v,
            rule_results=rule_results,
        )

    def generate_report(
        self, framework: str, tenant_id=None, period_days: int = 30, generated_by: str = "system"
    ) -> ComplianceReport:
        period_end = timezone.now()
        period_start = period_end - timedelta(days=period_days)

        profile = ComplianceProfile.objects.filter(
            framework=framework, tenant_id=tenant_id, is_active=True
        ).first()

        assessments = ComplianceAssessment.objects.filter(
            profile__framework=framework,
            tenant_id=tenant_id,
            assessed_at__range=(period_start, period_end),
        )
        open_violations = ComplianceViolation.objects.filter(
            rule__profile__framework=framework,
            tenant_id=tenant_id,
            status__in=[ViolationStatus.OPEN, ViolationStatus.ACKNOWLEDGED],
        )

        latest = assessments.order_by("-assessed_at").first()
        overall_score = latest.score if latest else 0
        overall_result = latest.result if latest else AssessmentResult.PENDING
        total_controls = profile.rules.filter(is_active=True).count() if profile else 0
        passing_controls = total_controls - open_violations.count()

        return ComplianceReport.objects.create(
            tenant_id=tenant_id,
            title=f"{framework.upper()} Compliance Report {period_start:%Y-%m-%d} to {period_end:%Y-%m-%d}",
            framework=framework,
            period_start=period_start,
            period_end=period_end,
            generated_by=generated_by,
            overall_score=overall_score,
            overall_result=overall_result,
            total_controls=total_controls,
            passing_controls=max(passing_controls, 0),
            open_violations=open_violations.count(),
            findings=[],
            recommendations=[],
        )


# ---------------------------------------------------------------------------
# ViolationService
# ---------------------------------------------------------------------------

class ViolationService:
    """Record and manage compliance violations."""

    def record(
        self, rule: ComplianceRule, tenant_id=None, description: str = "",
        resource_type: str = "", resource_id: str = "", evidence: dict = None,
    ) -> ComplianceViolation:
        return ComplianceViolation.objects.create(
            rule=rule,
            tenant_id=tenant_id,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            evidence=evidence or {},
        )

    def remediate(self, violation: ComplianceViolation, by: str, notes: str = "") -> None:
        violation.remediate(by=by, notes=notes)

    def accept_risk(self, violation: ComplianceViolation, by: str, reason: str) -> None:
        violation.accept_risk(by=by, reason=reason)


# ---------------------------------------------------------------------------
# EvidenceService
# ---------------------------------------------------------------------------

class EvidenceService:
    """Collect and package evidence records."""

    def collect(
        self, tenant_id, title: str, evidence_type: str,
        content: dict = None, collected_by: str = "",
        source_system: str = "", reference_id: str = "",
    ) -> EvidenceRecord:
        return EvidenceRecord.objects.create(
            tenant_id=tenant_id,
            title=title,
            evidence_type=evidence_type,
            content=content or {},
            collected_by=collected_by,
            source_system=source_system,
            reference_id=reference_id,
        )

    def create_package(
        self, tenant_id, name: str, purpose: str, created_by: str,
        record_ids: list = None, legal_hold_id=None, case_reference: str = "",
    ) -> EvidencePackage:
        pkg = EvidencePackage.objects.create(
            tenant_id=tenant_id,
            name=name,
            purpose=purpose,
            created_by=created_by,
            case_reference=case_reference,
            legal_hold_id=legal_hold_id,
        )
        if record_ids:
            pkg.records.set(EvidenceRecord.objects.filter(id__in=record_ids))
        return pkg

    def seal_package(self, package: EvidencePackage, sealed_by: str) -> None:
        package.seal(sealed_by=sealed_by)


# ---------------------------------------------------------------------------
# RetentionService
# ---------------------------------------------------------------------------

class RetentionService:
    """Enforce retention policies and schedule archival."""

    DEFAULT_POLICIES = [
        ("authentication", DataClassification.INTERNAL, 90, 365, 7, ComplianceFrameworkCode.ISO27001),
        ("clinical", DataClassification.PHI, 90, 365, 10, ComplianceFrameworkCode.HIPAA),
        ("financial", DataClassification.FINANCIAL, 90, 365, 7, ComplianceFrameworkCode.SOC2),
        ("government", DataClassification.GOVERNMENT_SENSITIVE, 90, 365, 10, ComplianceFrameworkCode.NCA_ECC),
        ("security", DataClassification.CONFIDENTIAL, 90, 365, 7, ComplianceFrameworkCode.ISO27001),
        ("ai", DataClassification.INTERNAL, 90, 180, 3, ComplianceFrameworkCode.ISO27001),
    ]

    def seed_default_policies(self, tenant_id=None) -> list:
        created = []
        for category, classification, hot, warm, cold_years, basis in self.DEFAULT_POLICIES:
            policy, is_new = AuditRetentionPolicy.objects.get_or_create(
                tenant_id=tenant_id,
                category=category,
                data_classification=classification,
                defaults={
                    "hot_retention_days": hot,
                    "warm_retention_days": warm,
                    "cold_retention_years": cold_years,
                    "compliance_basis": basis,
                },
            )
            if is_new:
                created.append(policy)
        return created

    def get_policy(self, category: str, classification: str, tenant_id=None) -> Optional[AuditRetentionPolicy]:
        return AuditRetentionPolicy.objects.filter(
            tenant_id=tenant_id, category=category, data_classification=classification, is_active=True
        ).first() or AuditRetentionPolicy.objects.filter(
            tenant_id=None, category=category, data_classification=classification, is_active=True
        ).first()


# ---------------------------------------------------------------------------
# AuditMetrics — Prometheus exposition
# ---------------------------------------------------------------------------

class AuditMetrics:
    """Platform-wide audit and compliance metrics."""

    def render_prometheus(self) -> str:
        from .models import AuditEvent, ComplianceViolation, LegalHold, AuditExport
        total_events = AuditEvent.objects.count()
        high_risk = AuditEvent.objects.filter(entry__is_high_risk=True).count()
        open_violations = ComplianceViolation.objects.filter(status=ViolationStatus.OPEN).count()
        critical_violations = ComplianceViolation.objects.filter(
            status=ViolationStatus.OPEN, rule__severity=ComplianceRuleSeverity.CRITICAL
        ).count()
        active_holds = LegalHold.objects.filter(status=LegalHoldStatus.ACTIVE).count()
        pending_exports = AuditExport.objects.filter(status="pending").count()

        lines = [
            "# HELP cybercom_audit_events_total Total audit events recorded",
            "# TYPE cybercom_audit_events_total counter",
            f"cybercom_audit_events_total {total_events}",
            "# HELP cybercom_audit_high_risk_events_total High-risk audit events",
            "# TYPE cybercom_audit_high_risk_events_total counter",
            f"cybercom_audit_high_risk_events_total {high_risk}",
            "# HELP cybercom_compliance_violations_open Open compliance violations",
            "# TYPE cybercom_compliance_violations_open gauge",
            f"cybercom_compliance_violations_open {open_violations}",
            "# HELP cybercom_compliance_violations_critical Open critical violations",
            "# TYPE cybercom_compliance_violations_critical gauge",
            f"cybercom_compliance_violations_critical {critical_violations}",
            "# HELP cybercom_legal_holds_active Active legal holds",
            "# TYPE cybercom_legal_holds_active gauge",
            f"cybercom_legal_holds_active {active_holds}",
            "# HELP cybercom_audit_exports_pending Pending audit exports",
            "# TYPE cybercom_audit_exports_pending gauge",
            f"cybercom_audit_exports_pending {pending_exports}",
        ]
        return "\n".join(lines) + "\n"
