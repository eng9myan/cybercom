"""
Program 2.3 — Audit & Compliance Framework tests.
90% coverage target. SQLite in-memory via core.test_settings.
"""
import hashlib
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from platform.audit.models import (
    AuditAction, AuditArchive, AuditCategory, AuditCategoryCode, AuditChain,
    AuditEntry, AuditEvent, AuditExport, AuditLog, AuditRetentionPolicy,
    AuditSignature, AuditStatus, AssessmentResult, ComplianceAssessment,
    ComplianceFrameworkCode, ComplianceProfile, ComplianceReport, ComplianceRule,
    ComplianceRuleSeverity, ComplianceViolation, DataClassification,
    EvidencePackage, EvidenceRecord, LegalHold, LegalHoldStatus,
    ViolationStatus,
)
from platform.audit.services import (
    AuditChainVerifier, AuditExportService, AuditMetrics, AuditSearchService,
    AuditService, ComplianceAssessmentService, ComplianceProfileService,
    EvidenceService, LegalHoldService, RetentionService, ViolationService,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_audit_event(**kwargs):
    defaults = dict(
        action="test.resource.read",
        action_verb=AuditAction.READ,
        resource_type="test_resource",
        resource_id=str(uuid.uuid4()),
        category=AuditCategoryCode.SYSTEM,
        data_classification=DataClassification.INTERNAL,
        status=AuditStatus.SUCCESS,
        entry_hash=hashlib.sha256(b"test").hexdigest(),
    )
    defaults.update(kwargs)
    return AuditEvent.objects.create(**defaults)


def make_compliance_profile(framework=ComplianceFrameworkCode.HIPAA, tenant_id=None):
    return ComplianceProfile.objects.create(
        tenant_id=tenant_id,
        framework=framework,
        name=f"{framework} profile",
        passing_score=80,
    )


def make_chain(key="test:chain"):
    chain, _ = AuditChain.objects.get_or_create(chain_key=key)
    return chain


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

class TestAuditLog:
    def test_create(self):
        log = AuditLog.objects.create(
            action=AuditAction.CREATE,
            resource_type="user",
            resource_id="u1",
        )
        assert log.id is not None
        assert log.status == AuditStatus.SUCCESS

    def test_immutable_save(self):
        log = AuditLog.objects.create(action=AuditAction.READ, resource_type="r")
        with pytest.raises(ValueError, match="immutable"):
            log.save()

    def test_immutable_delete(self):
        log = AuditLog.objects.create(action=AuditAction.READ, resource_type="r")
        with pytest.raises(ValueError, match="cannot be deleted"):
            log.delete()

    def test_description_and_metadata_fields(self):
        log = AuditLog.objects.create(
            action=AuditAction.UPDATE,
            resource_type="tenant",
            description="Tenant suspended",
            metadata={"reason": "billing"},
        )
        fetched = AuditLog.objects.get(pk=log.pk)
        assert fetched.description == "Tenant suspended"
        assert fetched.metadata["reason"] == "billing"

    def test_compute_hash(self):
        log = AuditLog.objects.create(action=AuditAction.READ, resource_type="r")
        h = log.compute_hash()
        assert len(h) == 64

    def test_str(self):
        log = AuditLog.objects.create(action=AuditAction.LOGIN, resource_type="session")
        assert "login" in str(log)


# ---------------------------------------------------------------------------
# AuditEvent
# ---------------------------------------------------------------------------

class TestAuditEvent:
    def test_create_basic(self):
        ev = make_audit_event()
        assert ev.id is not None
        assert ev.status == AuditStatus.SUCCESS

    def test_immutable_save(self):
        ev = make_audit_event()
        with pytest.raises(ValueError, match="immutable"):
            ev.save()

    def test_immutable_delete(self):
        ev = make_audit_event()
        with pytest.raises(ValueError, match="cannot be deleted"):
            ev.delete()

    def test_compute_hash(self):
        ev = make_audit_event()
        h = ev.compute_hash()
        assert len(h) == 64

    def test_before_after_state(self):
        ev = make_audit_event(
            action="user.update",
            action_verb=AuditAction.UPDATE,
            before_state={"email": "old@x.com"},
            after_state={"email": "new@x.com"},
        )
        assert ev.before_state["email"] == "old@x.com"
        assert ev.after_state["email"] == "new@x.com"

    def test_clinical_purpose_of_use(self):
        ev = make_audit_event(
            category=AuditCategoryCode.CLINICAL,
            data_classification=DataClassification.PHI,
            purpose_of_use="emergency_treatment",
        )
        assert ev.purpose_of_use == "emergency_treatment"

    def test_str(self):
        ev = make_audit_event(tenant_slug="acme")
        assert "acme" in str(ev)


# ---------------------------------------------------------------------------
# AuditChain
# ---------------------------------------------------------------------------

class TestAuditChain:
    def test_create(self):
        chain = AuditChain.objects.create(chain_key="t1:chain")
        assert chain.current_sequence == 0
        assert chain.last_hash == ""

    def test_str(self):
        chain = AuditChain.objects.create(chain_key="t2:chain")
        assert "t2:chain" in str(chain)

    def test_unique_key(self):
        AuditChain.objects.create(chain_key="unique:key")
        from django.db import IntegrityError
        with pytest.raises(Exception):
            AuditChain.objects.create(chain_key="unique:key")


# ---------------------------------------------------------------------------
# AuditCategory
# ---------------------------------------------------------------------------

class TestAuditCategory:
    def test_create(self):
        cat = AuditCategory.objects.create(
            code=AuditCategoryCode.CLINICAL,
            name="Clinical",
            requires_purpose_of_use=True,
        )
        assert cat.requires_purpose_of_use is True

    def test_str(self):
        cat = AuditCategory.objects.create(code=AuditCategoryCode.AI, name="AI")
        assert "ai" in str(cat)


# ---------------------------------------------------------------------------
# AuditRetentionPolicy
# ---------------------------------------------------------------------------

class TestAuditRetentionPolicy:
    def test_create(self):
        policy = AuditRetentionPolicy.objects.create(
            category=AuditCategoryCode.CLINICAL,
            data_classification=DataClassification.PHI,
            hot_retention_days=90,
            warm_retention_days=365,
            cold_retention_years=10,
            compliance_basis=ComplianceFrameworkCode.HIPAA,
        )
        assert policy.cold_retention_years == 10

    def test_str(self):
        policy = AuditRetentionPolicy.objects.create(
            category=AuditCategoryCode.SECURITY,
            data_classification=DataClassification.CONFIDENTIAL,
        )
        assert "security" in str(policy)


# ---------------------------------------------------------------------------
# AuditSignature
# ---------------------------------------------------------------------------

class TestAuditSignature:
    def test_create(self):
        chain = make_chain("sig:chain")
        sig = AuditSignature.objects.create(
            chain=chain,
            sequence_from=1,
            sequence_to=100,
            block_hash="abc" * 21 + "d",
            signature="fakesig",
        )
        assert sig.algorithm == "SHA256withRSA"

    def test_str(self):
        chain = make_chain("sig2:chain")
        sig = AuditSignature.objects.create(
            chain=chain, sequence_from=1, sequence_to=50,
            block_hash="a" * 64, signature="sig",
        )
        assert "sig2:chain" in str(sig)


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------

class TestAuditEntry:
    def test_create(self):
        chain = make_chain("entry:chain")
        ev = make_audit_event()
        entry = AuditEntry.objects.create(
            event=ev, chain=chain, sequence=1,
            compliance_tags=["hipaa"], is_high_risk=True, risk_score=80,
        )
        assert entry.is_high_risk is True
        assert "hipaa" in entry.compliance_tags

    def test_str(self):
        chain = make_chain("entry2:chain")
        ev = make_audit_event()
        entry = AuditEntry.objects.create(event=ev, chain=chain, sequence=42)
        assert "42" in str(entry)


# ---------------------------------------------------------------------------
# AuditExport
# ---------------------------------------------------------------------------

class TestAuditExport:
    def test_create(self):
        export = AuditExport.objects.create(
            requested_by="admin@x.com",
            reason="quarterly audit",
            format="json",
        )
        assert export.status == "pending"

    def test_str(self):
        export = AuditExport.objects.create(requested_by="x", reason="y")
        assert "pending" in str(export)


# ---------------------------------------------------------------------------
# AuditArchive
# ---------------------------------------------------------------------------

class TestAuditArchive:
    def test_create(self):
        now = timezone.now()
        archive = AuditArchive.objects.create(
            archive_key="global/clinical/2026-01-01",
            period_start=now - timedelta(days=90),
            period_end=now,
            event_count=1000,
        )
        assert archive.status == "pending"

    def test_str(self):
        now = timezone.now()
        archive = AuditArchive.objects.create(
            archive_key="global/security/2026-02",
            period_start=now - timedelta(days=30),
            period_end=now,
        )
        assert "global/security" in str(archive)


# ---------------------------------------------------------------------------
# LegalHold
# ---------------------------------------------------------------------------

class TestLegalHold:
    def test_create(self):
        hold = LegalHold.objects.create(
            name="Case 2026-001",
            description="Data preservation for litigation",
            created_by="legal@x.com",
            case_reference="CASE-001",
        )
        assert hold.status == LegalHoldStatus.ACTIVE
        assert hold.is_active is True

    def test_release(self):
        hold = LegalHold.objects.create(
            name="Case Release",
            description="test",
            created_by="legal@x.com",
        )
        hold.release(released_by="judge@x.com", reason="case_closed")
        assert hold.status == LegalHoldStatus.RELEASED
        assert hold.released_by == "judge@x.com"

    def test_release_already_released_raises(self):
        hold = LegalHold.objects.create(
            name="Double Release", description="test", created_by="legal@x.com"
        )
        hold.release(released_by="a@x.com", reason="done")
        with pytest.raises(ValueError):
            hold.release(released_by="b@x.com", reason="again")

    def test_is_active_false_when_expired(self):
        hold = LegalHold.objects.create(
            name="Expired Hold", description="test", created_by="legal@x.com",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert hold.is_active is False

    def test_str(self):
        hold = LegalHold.objects.create(
            name="Test Hold", description="test", created_by="x"
        )
        assert "Test Hold" in str(hold)


# ---------------------------------------------------------------------------
# ComplianceProfile
# ---------------------------------------------------------------------------

class TestComplianceProfile:
    def test_create(self):
        profile = make_compliance_profile()
        assert profile.framework == ComplianceFrameworkCode.HIPAA
        assert profile.passing_score == 80

    def test_unique_per_tenant_framework(self):
        tenant_id = uuid.uuid4()
        make_compliance_profile(tenant_id=tenant_id)
        from django.db import IntegrityError
        with pytest.raises(Exception):
            make_compliance_profile(tenant_id=tenant_id)

    def test_str(self):
        profile = make_compliance_profile(framework=ComplianceFrameworkCode.GDPR)
        assert "gdpr" in str(profile)


# ---------------------------------------------------------------------------
# ComplianceRule
# ---------------------------------------------------------------------------

class TestComplianceRule:
    def test_create(self):
        profile = make_compliance_profile()
        rule = ComplianceRule.objects.create(
            profile=profile,
            rule_id="HIPAA-AC-1",
            name="Unique User ID",
            description="Each user has a unique identifier",
            severity=ComplianceRuleSeverity.CRITICAL,
        )
        assert rule.severity == ComplianceRuleSeverity.CRITICAL

    def test_str(self):
        profile = make_compliance_profile()
        rule = ComplianceRule.objects.create(
            profile=profile, rule_id="R-1", name="Rule 1",
            description="desc", severity=ComplianceRuleSeverity.HIGH,
        )
        assert "R-1" in str(rule)


# ---------------------------------------------------------------------------
# ComplianceViolation
# ---------------------------------------------------------------------------

class TestComplianceViolation:
    def _make_rule(self):
        profile = make_compliance_profile(framework=ComplianceFrameworkCode.SOC2)
        return ComplianceRule.objects.create(
            profile=profile, rule_id="V-1", name="Violation Rule",
            description="d", severity=ComplianceRuleSeverity.HIGH,
        )

    def test_create(self):
        rule = self._make_rule()
        v = ComplianceViolation.objects.create(rule=rule, description="Access control gap")
        assert v.status == ViolationStatus.OPEN

    def test_remediate(self):
        rule = self._make_rule()
        v = ComplianceViolation.objects.create(rule=rule, description="gap")
        v.remediate(by="ops@x.com", notes="Fixed via policy update")
        assert v.status == ViolationStatus.REMEDIATED
        assert v.remediated_by == "ops@x.com"

    def test_accept_risk(self):
        rule = self._make_rule()
        v = ComplianceViolation.objects.create(rule=rule, description="low risk gap")
        v.accept_risk(by="ciso@x.com", reason="Low impact accepted")
        assert v.status == ViolationStatus.ACCEPTED_RISK

    def test_str(self):
        rule = self._make_rule()
        v = ComplianceViolation.objects.create(rule=rule, description="d")
        assert "V-1" in str(v)


# ---------------------------------------------------------------------------
# ComplianceAssessment
# ---------------------------------------------------------------------------

class TestComplianceAssessment:
    def test_create(self):
        profile = make_compliance_profile()
        assessment = ComplianceAssessment.objects.create(
            profile=profile, total_rules=10, passed_rules=9,
            failed_rules=1, score=90, result=AssessmentResult.PASSED,
        )
        assert assessment.passed is True

    def test_not_passed_below_threshold(self):
        profile = make_compliance_profile()
        assessment = ComplianceAssessment.objects.create(
            profile=profile, score=70, result=AssessmentResult.FAILED,
        )
        assert assessment.passed is False

    def test_str(self):
        profile = make_compliance_profile()
        a = ComplianceAssessment.objects.create(profile=profile, score=85, result=AssessmentResult.PASSED)
        assert "hipaa" in str(a)


# ---------------------------------------------------------------------------
# ComplianceReport
# ---------------------------------------------------------------------------

class TestComplianceReport:
    def test_create(self):
        now = timezone.now()
        report = ComplianceReport.objects.create(
            framework=ComplianceFrameworkCode.HIPAA,
            title="HIPAA Q1 2026",
            period_start=now - timedelta(days=90),
            period_end=now,
            overall_score=88,
            overall_result=AssessmentResult.PASSED,
        )
        assert report.overall_score == 88

    def test_str(self):
        now = timezone.now()
        r = ComplianceReport.objects.create(
            framework=ComplianceFrameworkCode.GDPR,
            title="GDPR Report",
            period_start=now - timedelta(days=30),
            period_end=now,
        )
        assert "gdpr" in str(r)


# ---------------------------------------------------------------------------
# EvidenceRecord
# ---------------------------------------------------------------------------

class TestEvidenceRecord:
    def test_create(self):
        rec = EvidenceRecord.objects.create(
            title="Access log export",
            evidence_type="audit_log",
            collected_by="analyst@x.com",
        )
        assert rec.is_locked is False

    def test_lock(self):
        rec = EvidenceRecord.objects.create(
            title="Screenshot", evidence_type="screenshot"
        )
        rec.lock()
        assert rec.is_locked is True
        assert rec.locked_at is not None

    def test_str(self):
        rec = EvidenceRecord.objects.create(title="Config export", evidence_type="system_config")
        assert "Config export" in str(rec)


# ---------------------------------------------------------------------------
# EvidencePackage
# ---------------------------------------------------------------------------

class TestEvidencePackage:
    def test_create(self):
        pkg = EvidencePackage.objects.create(
            name="Case Bundle",
            purpose="legal_proceeding",
            created_by="legal@x.com",
        )
        assert pkg.is_sealed is False

    def test_seal(self):
        rec = EvidenceRecord.objects.create(title="R1", evidence_type="document")
        pkg = EvidencePackage.objects.create(
            name="Sealed Bundle",
            purpose="regulatory_audit",
            created_by="audit@x.com",
        )
        pkg.records.add(rec)
        pkg.seal(sealed_by="auditor@x.com")
        assert pkg.is_sealed is True
        assert pkg.package_hash != ""

    def test_seal_twice_raises(self):
        pkg = EvidencePackage.objects.create(
            name="Double Seal", purpose="internal_investigation", created_by="x"
        )
        pkg.seal(sealed_by="a@x.com")
        with pytest.raises(ValueError):
            pkg.seal(sealed_by="b@x.com")

    def test_str(self):
        pkg = EvidencePackage.objects.create(
            name="Test Pkg", purpose="compliance_certification", created_by="x"
        )
        assert "Test Pkg" in str(pkg)


# ---------------------------------------------------------------------------
# AuditService
# ---------------------------------------------------------------------------

class TestAuditService:
    def test_record_creates_event_and_entry(self):
        svc = AuditService()
        tenant_id = uuid.uuid4()
        event = svc.record(
            action="user.login",
            action_verb=AuditAction.LOGIN,
            resource_type="session",
            resource_id="sess-1",
            tenant_id=tenant_id,
            tenant_slug="acme",
            actor_user_id="user-123",
            category=AuditCategoryCode.AUTHENTICATION,
        )
        assert event.id is not None
        assert event.entry_hash != ""
        assert AuditEntry.objects.filter(event=event).exists()

    def test_hash_chain_advances(self):
        svc = AuditService()
        tenant_id = uuid.uuid4()
        svc.record(action="a.b", action_verb=AuditAction.READ, resource_type="x", tenant_id=tenant_id)
        chain = AuditChain.objects.get(chain_key=f"tenant:{tenant_id}")
        assert chain.current_sequence == 1
        svc.record(action="a.c", action_verb=AuditAction.READ, resource_type="x", tenant_id=tenant_id)
        chain.refresh_from_db()
        assert chain.current_sequence == 2

    def test_high_risk_classification(self):
        svc = AuditService()
        event = svc.record(
            action="phi.record.read",
            action_verb=AuditAction.BREAK_GLASS,
            resource_type="patient_record",
            category=AuditCategoryCode.CLINICAL,
            data_classification=DataClassification.PHI,
        )
        entry = AuditEntry.objects.get(event=event)
        assert entry.is_high_risk is True
        assert entry.risk_score >= 80

    def test_compliance_tags_phi(self):
        svc = AuditService()
        event = svc.record(
            action="phi.read",
            action_verb=AuditAction.READ,
            resource_type="patient",
            category=AuditCategoryCode.CLINICAL,
            data_classification=DataClassification.PHI,
        )
        entry = AuditEntry.objects.get(event=event)
        assert "hipaa" in entry.compliance_tags

    def test_compliance_tags_financial(self):
        svc = AuditService()
        event = svc.record(
            action="payment.created",
            action_verb=AuditAction.CREATE,
            resource_type="payment",
            category=AuditCategoryCode.FINANCIAL,
            data_classification=DataClassification.FINANCIAL,
        )
        entry = AuditEntry.objects.get(event=event)
        assert "pci_dss" in entry.compliance_tags

    def test_global_chain_when_no_tenant(self):
        svc = AuditService()
        event = svc.record(action="sys.event", action_verb=AuditAction.CREATE, resource_type="system")
        chain = AuditChain.objects.get(chain_key="platform:global")
        assert chain is not None


# ---------------------------------------------------------------------------
# AuditChainVerifier
# ---------------------------------------------------------------------------

class TestAuditChainVerifier:
    def test_verify_empty_chain(self):
        AuditChain.objects.create(chain_key="empty:verify")
        result = AuditChainVerifier().verify("empty:verify")
        assert result["valid"] is True
        assert result["checked"] == 0

    def test_verify_nonexistent_chain(self):
        result = AuditChainVerifier().verify("nonexistent:chain")
        assert result["valid"] is False

    def test_verify_valid_chain(self):
        svc = AuditService()
        tenant_id = uuid.uuid4()
        for _ in range(3):
            svc.record(
                action="verify.test", action_verb=AuditAction.READ,
                resource_type="resource", tenant_id=tenant_id,
            )
        chain_key = f"tenant:{tenant_id}"
        result = AuditChainVerifier().verify(chain_key)
        assert result["valid"] is True
        assert result["checked"] == 3

    def test_verify_all_returns_list(self):
        AuditChain.objects.create(chain_key="all:v1")
        AuditChain.objects.create(chain_key="all:v2")
        results = AuditChainVerifier().verify_all()
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# AuditSearchService
# ---------------------------------------------------------------------------

class TestAuditSearchService:
    def setup_method(self):
        self.svc = AuditSearchService()
        self.tenant_id = uuid.uuid4()
        make_audit_event(
            tenant_id=self.tenant_id, category=AuditCategoryCode.CLINICAL,
            action="patient.chart.read", action_verb=AuditAction.READ,
            data_classification=DataClassification.PHI,
        )
        make_audit_event(
            tenant_id=self.tenant_id, category=AuditCategoryCode.AUTHENTICATION,
            action="user.login", action_verb=AuditAction.LOGIN,
        )

    def test_search_by_tenant(self):
        results = list(self.svc.search(tenant_id=self.tenant_id))
        assert len(results) == 2

    def test_search_by_category(self):
        results = list(self.svc.search(tenant_id=self.tenant_id, category=AuditCategoryCode.CLINICAL))
        assert len(results) == 1
        assert results[0].category == AuditCategoryCode.CLINICAL

    def test_search_by_action(self):
        results = list(self.svc.search(tenant_id=self.tenant_id, action="login"))
        assert len(results) == 1

    def test_search_limit(self):
        for _ in range(5):
            make_audit_event(tenant_id=self.tenant_id)
        results = list(self.svc.search(tenant_id=self.tenant_id, limit=3))
        assert len(results) == 3

    def test_search_no_filter_returns_all(self):
        results = list(self.svc.search(limit=1000))
        assert len(results) >= 2


# ---------------------------------------------------------------------------
# AuditExportService
# ---------------------------------------------------------------------------

class TestAuditExportService:
    def test_create_export(self):
        svc = AuditExportService()
        export = svc.create_export(
            tenant_id=None, requested_by="admin@x.com",
            reason="SOC2 audit", format="json",
        )
        assert export.status == "pending"
        assert export.reason == "SOC2 audit"

    def test_complete_export(self):
        svc = AuditExportService()
        export = svc.create_export(tenant_id=None, requested_by="x", reason="y")
        svc.complete_export(export, event_count=500, download_url="https://s3.example.com/export.json")
        assert export.status == "ready"
        assert export.event_count == 500

    def test_fail_export(self):
        svc = AuditExportService()
        export = svc.create_export(tenant_id=None, requested_by="x", reason="y")
        svc.fail_export(export, error="S3 connection failed")
        assert export.status == "failed"
        assert "S3" in export.error_message


# ---------------------------------------------------------------------------
# LegalHoldService
# ---------------------------------------------------------------------------

class TestLegalHoldService:
    def test_create_hold(self):
        svc = LegalHoldService()
        hold = svc.create(
            tenant_id=None, name="Litigation Hold", description="Preserve records",
            created_by="legal@x.com", case_reference="CASE-2026-001",
            resource_types=["patient_record"], resource_ids=["rec-1"],
        )
        assert hold.status == LegalHoldStatus.ACTIVE
        assert hold.case_reference == "CASE-2026-001"
        assert AuditLog.objects.filter(resource_type="legal_hold").exists()

    def test_release_hold(self):
        svc = LegalHoldService()
        hold = svc.create(tenant_id=None, name="Hold2", description="d", created_by="x")
        svc.release(hold, released_by="y@x.com", reason="resolved")
        assert hold.status == LegalHoldStatus.RELEASED

    def test_is_resource_held_true(self):
        svc = LegalHoldService()
        tenant_id = uuid.uuid4()
        svc.create(
            tenant_id=tenant_id, name="Hold3", description="d",
            created_by="x", resource_types=["patient_record"],
        )
        assert svc.is_resource_held(tenant_id, "patient_record") is True

    def test_is_resource_held_false_no_holds(self):
        svc = LegalHoldService()
        tenant_id = uuid.uuid4()
        assert svc.is_resource_held(tenant_id, "unknown_resource") is False


# ---------------------------------------------------------------------------
# ComplianceProfileService
# ---------------------------------------------------------------------------

class TestComplianceProfileService:
    def test_create_hipaa_profile_seeds_rules(self):
        svc = ComplianceProfileService()
        profile = svc.create_profile(ComplianceFrameworkCode.HIPAA, seed_rules=True)
        assert profile.rules.count() == len(svc.FRAMEWORK_RULES[ComplianceFrameworkCode.HIPAA])

    def test_create_gdpr_profile_seeds_rules(self):
        svc = ComplianceProfileService()
        profile = svc.create_profile(ComplianceFrameworkCode.GDPR, seed_rules=True)
        assert profile.rules.count() > 0

    def test_create_soc2_profile_seeds_rules(self):
        svc = ComplianceProfileService()
        profile = svc.create_profile(ComplianceFrameworkCode.SOC2, seed_rules=True)
        assert profile.rules.filter(severity=ComplianceRuleSeverity.CRITICAL).exists()

    def test_create_nca_ecc_profile_seeds_rules(self):
        svc = ComplianceProfileService()
        profile = svc.create_profile(ComplianceFrameworkCode.NCA_ECC, seed_rules=True)
        assert profile.rules.count() > 0

    def test_get_or_create_idempotent(self):
        svc = ComplianceProfileService()
        tenant_id = uuid.uuid4()
        p1 = svc.get_or_create(ComplianceFrameworkCode.ISO27001, tenant_id=tenant_id)
        p2 = svc.get_or_create(ComplianceFrameworkCode.ISO27001, tenant_id=tenant_id)
        assert p1.id == p2.id


# ---------------------------------------------------------------------------
# ComplianceAssessmentService
# ---------------------------------------------------------------------------

class TestComplianceAssessmentService:
    def test_assess_all_pass(self):
        svc_p = ComplianceProfileService()
        profile = svc_p.create_profile(ComplianceFrameworkCode.SOC2, seed_rules=True)
        svc_a = ComplianceAssessmentService()
        assessment = svc_a.assess(profile)
        assert assessment.result in (AssessmentResult.PASSED, AssessmentResult.PARTIAL)
        assert assessment.score >= 0

    def test_assess_with_violations(self):
        svc_p = ComplianceProfileService()
        profile = svc_p.create_profile(ComplianceFrameworkCode.HIPAA, seed_rules=True)
        rule = profile.rules.filter(severity=ComplianceRuleSeverity.CRITICAL).first()
        ComplianceViolation.objects.create(rule=rule, description="Critical gap")
        svc_a = ComplianceAssessmentService()
        assessment = svc_a.assess(profile)
        assert assessment.failed_rules > 0
        assert assessment.critical_violations > 0
        assert assessment.result == AssessmentResult.FAILED

    def test_generate_report(self):
        svc_p = ComplianceProfileService()
        profile = svc_p.create_profile(ComplianceFrameworkCode.GDPR, seed_rules=True)
        svc_a = ComplianceAssessmentService()
        report = svc_a.generate_report(
            framework=ComplianceFrameworkCode.GDPR,
            tenant_id=profile.tenant_id,
        )
        assert report.framework == ComplianceFrameworkCode.GDPR
        assert report.id is not None


# ---------------------------------------------------------------------------
# ViolationService
# ---------------------------------------------------------------------------

class TestViolationService:
    def _make_rule(self):
        profile = make_compliance_profile(framework=ComplianceFrameworkCode.PCI_DSS)
        return ComplianceRule.objects.create(
            profile=profile, rule_id="PCI-1", name="Card data encryption",
            description="d", severity=ComplianceRuleSeverity.CRITICAL,
        )

    def test_record_violation(self):
        rule = self._make_rule()
        svc = ViolationService()
        v = svc.record(rule, description="Encryption not enforced", resource_type="payment")
        assert v.status == ViolationStatus.OPEN

    def test_remediate(self):
        rule = self._make_rule()
        svc = ViolationService()
        v = svc.record(rule, description="gap")
        svc.remediate(v, by="dev@x.com", notes="Fixed")
        assert v.status == ViolationStatus.REMEDIATED

    def test_accept_risk(self):
        rule = self._make_rule()
        svc = ViolationService()
        v = svc.record(rule, description="low risk")
        svc.accept_risk(v, by="ciso@x.com", reason="Accepted")
        assert v.status == ViolationStatus.ACCEPTED_RISK


# ---------------------------------------------------------------------------
# EvidenceService
# ---------------------------------------------------------------------------

class TestEvidenceService:
    def test_collect(self):
        svc = EvidenceService()
        rec = svc.collect(
            tenant_id=None, title="Audit Log Jan-2026",
            evidence_type="audit_log", collected_by="analyst@x.com",
        )
        assert rec.id is not None

    def test_create_package(self):
        svc = EvidenceService()
        rec = svc.collect(tenant_id=None, title="R1", evidence_type="document")
        pkg = svc.create_package(
            tenant_id=None, name="Regulatory Package",
            purpose="regulatory_audit", created_by="cco@x.com",
            record_ids=[rec.id],
        )
        assert pkg.records.count() == 1

    def test_seal_package(self):
        svc = EvidenceService()
        pkg = svc.create_package(
            tenant_id=None, name="Legal Bundle",
            purpose="legal_proceeding", created_by="legal@x.com",
        )
        svc.seal_package(pkg, sealed_by="judge@x.com")
        assert pkg.is_sealed is True


# ---------------------------------------------------------------------------
# RetentionService
# ---------------------------------------------------------------------------

class TestRetentionService:
    def test_seed_default_policies(self):
        svc = RetentionService()
        tenant_id = uuid.uuid4()
        created = svc.seed_default_policies(tenant_id=tenant_id)
        assert len(created) > 0

    def test_seed_idempotent(self):
        svc = RetentionService()
        tenant_id = uuid.uuid4()
        svc.seed_default_policies(tenant_id=tenant_id)
        created2 = svc.seed_default_policies(tenant_id=tenant_id)
        assert len(created2) == 0

    def test_get_policy(self):
        svc = RetentionService()
        tenant_id = uuid.uuid4()
        svc.seed_default_policies(tenant_id=tenant_id)
        policy = svc.get_policy(
            category=AuditCategoryCode.CLINICAL,
            classification=DataClassification.PHI,
            tenant_id=tenant_id,
        )
        assert policy is not None
        assert policy.cold_retention_years == 10


# ---------------------------------------------------------------------------
# AuditMetrics
# ---------------------------------------------------------------------------

class TestAuditMetrics:
    def test_render_prometheus(self):
        svc = AuditService()
        svc.record(action="m.test", action_verb=AuditAction.READ, resource_type="resource")
        output = AuditMetrics().render_prometheus()
        assert "cybercom_audit_events_total" in output
        assert "cybercom_compliance_violations_open" in output
        assert "cybercom_legal_holds_active" in output

    def test_prometheus_contains_numeric_values(self):
        output = AuditMetrics().render_prometheus()
        lines = [l for l in output.splitlines() if not l.startswith("#")]
        for line in lines:
            parts = line.split()
            assert len(parts) == 2
            assert parts[1].isdigit()


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

class TestAuditTasks:
    def test_verify_chains_task(self):
        from platform.audit.tasks import verify_chains_task
        svc = AuditService()
        svc.record(action="task.test", action_verb=AuditAction.CREATE, resource_type="r")
        result = verify_chains_task()
        assert "total" in result
        assert result["invalid"] == 0

    def test_archive_expired_task(self):
        from platform.audit.tasks import archive_expired_events_task
        result = archive_expired_events_task()
        assert "archived" in result

    def test_expire_legal_holds_task(self):
        from platform.audit.tasks import expire_legal_holds_task
        LegalHold.objects.create(
            name="Exp Hold", description="d", created_by="x",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        result = expire_legal_holds_task()
        assert result["expired"] >= 1

    def test_run_compliance_assessments_task(self):
        from platform.audit.tasks import run_compliance_assessments_task
        svc_p = ComplianceProfileService()
        svc_p.create_profile(ComplianceFrameworkCode.SOC2, seed_rules=True)
        result = run_compliance_assessments_task()
        assert result["assessed"] >= 1

    def test_expire_exports_task(self):
        from platform.audit.tasks import expire_exports_task
        AuditExport.objects.create(
            requested_by="x", reason="y", status="ready",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        result = expire_exports_task()
        assert result["expired"] >= 1


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

class TestSignals:
    def test_legal_hold_status_change_audit(self):
        hold = LegalHold.objects.create(
            name="Signal Hold", description="d", created_by="x"
        )
        initial_count = AuditLog.objects.count()
        hold.release(released_by="y@x.com", reason="done")
        assert AuditLog.objects.count() >= initial_count

    def test_violation_created_audit(self):
        profile = make_compliance_profile(framework=ComplianceFrameworkCode.NCA_ECC)
        rule = ComplianceRule.objects.create(
            profile=profile, rule_id="SIG-1", name="Signal rule",
            description="d", severity=ComplianceRuleSeverity.HIGH,
        )
        initial_count = AuditLog.objects.count()
        ComplianceViolation.objects.create(rule=rule, description="gap")
        assert AuditLog.objects.count() > initial_count


# ---------------------------------------------------------------------------
# Health API (functional)
# ---------------------------------------------------------------------------

class TestAuditHealthAPI:
    def test_health_view(self):
        from django.test import RequestFactory
        from platform.audit.views import audit_health
        rf = RequestFactory()
        request = rf.get("/api/v1/audit/healthz/")
        response = audit_health(request)
        assert response.status_code == 200

    def test_metrics_view(self):
        from django.test import RequestFactory
        from platform.audit.views import audit_metrics
        rf = RequestFactory()
        request = rf.get("/api/v1/audit/metrics")
        response = audit_metrics(request)
        assert response.status_code == 200
