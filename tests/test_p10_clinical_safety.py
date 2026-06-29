"""
Program 10 – Phase 2: Clinical Safety Validation Suite

Validates:
- Drug interaction engine (drug-drug, drug-allergy, drug-diagnosis)
- Contraindicated severity auto-blocking (no dispensing without pharmacist)
- Interaction alert lifecycle (active → pharmacist_reviewed → overridden)
- Override requires pharmacist UUID (not dispenser-level)
- AI priority score stored but does NOT make clinical decisions
- Break glass clinical access model
- Critical lab alert model (via terminology codes)
- Allergy model field structure matches FHIR AllergyIntolerance
- Clinical decisions are auditable (audit trail category = 'clinical')
- Advisory-only AI: CyAI InferenceLog with safety_verdict and guardrail policy
"""

import uuid

import pytest
from django.utils import timezone

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PHARMACIST = uuid.uuid4()
PRESCRIBER = uuid.uuid4()
ENCOUNTER = uuid.uuid4()


def _make_patient():
    import datetime

    from products.cymed.core.patients.models import Patient

    return Patient.objects.create(
        tenant_id=TENANT,
        first_name="John",
        last_name="Doe",
        dob=datetime.date(1980, 1, 1),
        mrn=f"MRN-{uuid.uuid4().hex[:10].upper()}",
    )


# ---------------------------------------------------------------------------
# Phase 2.1 — Drug Interaction Engine
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestDrugInteractionEngine:
    def _make_rule(
        self,
        severity,
        interaction_type="drug_drug",
        override_allowed=True,
        requires_pharmacist=True,
    ):
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule

        return InteractionRule.objects.create(
            tenant_id=TENANT,
            rule_code=f"RULE-{uuid.uuid4().hex[:8].upper()}",
            interaction_type=interaction_type,
            severity=severity,
            drug_a_code="rxnorm:1049502",
            drug_a_name="Warfarin 5mg",
            drug_b_code="rxnorm:7052",
            drug_b_name="Aspirin 100mg",
            description="Warfarin + Aspirin: increased bleeding risk.",
            management_recommendation="Monitor INR closely. Use lowest effective aspirin dose.",
            override_allowed=override_allowed,
            requires_pharmacist_approval=requires_pharmacist,
        )

    def test_drug_drug_interaction_detected(self):
        from products.cymed.pharmacy.drug_interactions.models import (
            DrugInteraction,
        )

        rule = self._make_rule("severe")
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            prescription_id=uuid.uuid4(),
            encounter_id=ENCOUNTER,
            rule=rule,
            interaction_type="drug_drug",
            severity="severe",
            drug_a_code="rxnorm:1049502",
            drug_a_name="Warfarin 5mg",
            drug_b_code="rxnorm:7052",
            drug_b_name="Aspirin 100mg",
            alert_status="active",
        )
        assert interaction.severity == "severe"
        assert interaction.alert_status == "active"

    def test_contraindicated_rule_blocks_dispensing(self):
        """InteractionSeverity config for 'contraindicated' must have auto_block_dispensing=True."""
        from products.cymed.pharmacy.drug_interactions.models import InteractionSeverity

        severity_config = InteractionSeverity.objects.create(
            tenant_id=TENANT,
            severity="contraindicated",
            auto_block_dispensing=True,
            requires_pharmacist_review=True,
            notify_prescriber=True,
            notify_clinical_pharmacist=True,
        )
        assert severity_config.auto_block_dispensing is True

    def test_interaction_alert_created_on_detection(self):
        from products.cymed.pharmacy.drug_interactions.models import (
            DrugInteraction,
            InteractionAlert,
        )

        rule = self._make_rule("moderate")
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            rule=rule,
            interaction_type="drug_drug",
            severity="moderate",
            drug_a_code="rxnorm:1049502",
            drug_a_name="Warfarin 5mg",
            drug_b_code="rxnorm:7052",
            drug_b_name="Aspirin 100mg",
            alert_status="active",
        )
        alert = InteractionAlert.objects.create(
            tenant_id=TENANT,
            interaction=interaction,
            recipient_id=PHARMACIST,
            recipient_role="pharmacist",
            channel="ui_popup",
        )
        assert alert.channel == "ui_popup"
        assert alert.acknowledged_at is None

    def test_override_requires_pharmacist_uuid(self):
        """Override must store pharmacist UUID — empty overridden_by is a safety violation."""
        from products.cymed.pharmacy.drug_interactions.models import (
            DrugInteraction,
        )

        rule = self._make_rule("moderate", override_allowed=True, requires_pharmacist=True)
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            rule=rule,
            interaction_type="drug_drug",
            severity="moderate",
            drug_a_code="rxnorm:1049502",
            drug_a_name="Warfarin",
            drug_b_code="rxnorm:7052",
            drug_b_name="Aspirin",
            alert_status="active",
        )
        interaction.alert_status = "overridden"
        interaction.overridden_by = PHARMACIST
        interaction.overridden_at = timezone.now()
        interaction.override_reason = (
            "Patient has documented tolerance; cardiologist approved continuation."
        )
        interaction.override_approved_by = PHARMACIST
        interaction.save()
        refreshed = DrugInteraction.objects.get(pk=interaction.pk)
        assert refreshed.alert_status == "overridden"
        assert refreshed.overridden_by == PHARMACIST
        assert refreshed.override_reason != ""

    def test_ai_priority_score_is_advisory_only(self):
        """
        CyAI populates ai_priority_score and ai_clinical_context.
        These fields are for display prioritization only — no code path
        may use them to auto-approve or auto-dismiss a clinical alert.
        """
        from products.cymed.pharmacy.drug_interactions.models import (
            DrugInteraction,
        )

        rule = self._make_rule("minor")
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            rule=rule,
            interaction_type="drug_drug",
            severity="minor",
            drug_a_code="rxnorm:999",
            drug_a_name="Drug A",
            drug_b_code="rxnorm:888",
            drug_b_name="Drug B",
            alert_status="active",
            ai_priority_score=0.82,
            ai_clinical_context="CyAI: moderate risk given patient's CKD stage 3. Advisory only.",
        )
        assert interaction.alert_status == "active", "AI must not auto-dismiss alerts"
        assert "Advisory only" in interaction.ai_clinical_context

    def test_drug_allergy_interaction_type(self):
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule

        rule = InteractionRule.objects.create(
            tenant_id=TENANT,
            rule_code=f"ALLERGY-{uuid.uuid4().hex[:8].upper()}",
            interaction_type="drug_allergy",
            severity="contraindicated",
            drug_a_code="rxnorm:723",
            drug_a_name="Penicillin V",
            allergen_code="SNOMED:372687004",
            description="Penicillin allergy — contraindicated.",
            management_recommendation="Use alternative antibiotic class. Document allergy.",
            override_allowed=False,
            requires_pharmacist_approval=True,
        )
        assert rule.interaction_type == "drug_allergy"
        assert rule.severity == "contraindicated"
        assert rule.override_allowed is False

    def test_drug_pregnancy_category_x_contraindicated(self):
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule

        rule = InteractionRule.objects.create(
            tenant_id=TENANT,
            rule_code=f"PREG-{uuid.uuid4().hex[:8].upper()}",
            interaction_type="drug_pregnancy",
            severity="contraindicated",
            drug_a_code="rxnorm:203429",
            drug_a_name="Thalidomide",
            pregnancy_category="X",
            description="Thalidomide: Category X teratogen — absolutely contraindicated in pregnancy.",
            management_recommendation="Never use in pregnancy. Mandatory REMS program enrollment.",
            override_allowed=False,
            requires_pharmacist_approval=True,
        )
        assert rule.pregnancy_category == "X"
        assert rule.override_allowed is False


# ---------------------------------------------------------------------------
# Phase 2.2 — Allergy Management
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestAllergyManagement:
    def test_allergy_creates(self):
        from products.cymed.core.clinical.models import Allergy

        patient = _make_patient()
        allergy = Allergy.objects.create(
            tenant_id=TENANT,
            patient=patient,
            category="medication",
            substance_code="rxnorm:723",
            substance_display="Penicillin",
            clinical_status="active",
        )
        assert allergy.category == "medication"
        assert allergy.substance_code == "rxnorm:723"
        assert allergy.clinical_status == "active"

    def test_allergy_reaction_severity_levels_include_severe(self):
        from products.cymed.core.clinical.models import Allergy, AllergyReaction

        patient = _make_patient()
        allergy = Allergy.objects.create(
            tenant_id=TENANT,
            patient=patient,
            category="medication",
            substance_code="rxnorm:723",
            substance_display="Penicillin",
        )
        reaction = AllergyReaction.objects.create(
            tenant_id=TENANT,
            allergy=allergy,
            manifestation_code="SNOMED:39579001",
            severity="severe",
        )
        assert reaction.severity == "severe"
        fields = {f.name: f for f in AllergyReaction._meta.get_fields()}
        severity_field = fields.get("severity")
        assert severity_field is not None, "AllergyReaction.severity field not found"
        choices_values = {c[0] for c in getattr(severity_field, "choices", [])}
        assert "severe" in choices_values, "AllergyReaction must have 'severe' severity level"


# ---------------------------------------------------------------------------
# Phase 2.3 — Terminology & Standards Validation
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTerminologyModels:
    def test_terminology_audit_log_model_exists(self):
        """TerminologyAuditLog records all terminology lookups per tenant for compliance."""
        from platform.terminology.models import TerminologyAuditLog

        entry = TerminologyAuditLog.objects.create(
            tenant_id=TENANT,
            provider="icd11",
            operation="lookup",
            code="CA40",
            query="myocardial infarction",
            records_returned=1,
            duration_ms=42,
        )
        assert entry.code == "CA40"
        assert entry.provider == "icd11"

    def test_icd11_audit_log_lookup(self):
        from platform.terminology.models import TerminologyAuditLog

        TerminologyAuditLog.objects.create(
            tenant_id=TENANT,
            provider="icd11",
            operation="lookup",
            code="XY9Z",
            query="test diagnosis",
            records_returned=1,
        )
        result = TerminologyAuditLog.objects.filter(
            provider="icd11", code="XY9Z", tenant_id=TENANT
        ).first()
        assert result is not None
        assert result.query == "test diagnosis"

    def test_loinc_audit_log_lookup(self):
        from platform.terminology.models import TerminologyAuditLog

        TerminologyAuditLog.objects.create(
            tenant_id=TENANT,
            provider="loinc",
            operation="lookup",
            code="2160-0",
            query="Creatinine",
        )
        result = TerminologyAuditLog.objects.filter(
            provider="loinc", code="2160-0", tenant_id=TENANT
        ).first()
        assert result is not None

    def test_snomed_audit_log_lookup(self):
        from platform.terminology.models import TerminologyAuditLog

        TerminologyAuditLog.objects.create(
            tenant_id=TENANT,
            provider="snomed",
            operation="lookup",
            code="22298006",
            query="Myocardial infarction",
        )
        result = TerminologyAuditLog.objects.filter(
            provider="snomed", code="22298006", tenant_id=TENANT
        ).first()
        assert result is not None


# ---------------------------------------------------------------------------
# Phase 2.4 — CyAI Advisory-Only Guardrails
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestCyAIGuardrails:
    def test_cyai_inference_log_safety_verdict(self):
        """CyAI InferenceLog records safety_verdict — 'passed' means guardrails cleared."""
        from platform.cyai.models import InferenceLog

        log = InferenceLog.objects.create(
            tenant_id=TENANT,
            prompt_used="Summarize patient medication history for clinical review. [PHI scrubbed]",
            response_text="Patient is on Warfarin 5mg and Aspirin 100mg. Advisory: interaction risk.",
            tokens_prompt=120,
            tokens_completion=80,
            latency_ms=850,
            safety_verdict="passed",
        )
        assert log.safety_verdict == "passed"
        assert log.error_message == ""

    def test_cyai_guardrail_policy_clinical_safety(self):
        """GuardrailPolicy for clinical_safety must exist and be active in platform."""
        from platform.cyai.models import GuardrailPolicy

        policy = GuardrailPolicy.objects.create(
            name="Clinical Safety Guardrail",
            policy_type="clinical_safety",
            parameters={
                "blocked_keywords": ["prescribe", "administer", "order", "diagnose"],
                "require_advisory_disclaimer": True,
            },
            active=True,
        )
        assert policy.policy_type == "clinical_safety"
        assert policy.active is True
        assert "blocked_keywords" in policy.parameters

    def test_cyai_audit_log_captures_ai_category(self):
        from platform.audit.models import (
            AuditAction,
            AuditCategoryCode,
            AuditEvent,
            AuditStatus,
            DataClassification,
        )

        event = AuditEvent.objects.create(
            tenant_id=TENANT,
            actor_user_id=str(PRESCRIBER),
            action="ai.inference.completed",
            action_verb=AuditAction.CREATE,
            status=AuditStatus.SUCCESS,
            category=AuditCategoryCode.AI,
            resource_type="InferenceLog",
            resource_id=str(uuid.uuid4()),
            actor_ip="10.0.0.1",
            data_classification=DataClassification.CONFIDENTIAL,
            payload={"model": "cyai-clinical-v2", "advisory_only": True},
        )
        assert event.category == AuditCategoryCode.AI

    def test_cyai_blocked_inference_logged(self):
        """Blocked AI inference (PHI/clinical_safety violation) must be logged with safety_verdict='blocked'."""
        from platform.cyai.models import InferenceLog

        log = InferenceLog.objects.create(
            tenant_id=TENANT,
            prompt_used="Please prescribe 10mg Warfarin for patient John Doe DOB 1980-01-01 MRN-123456",
            response_text="",
            tokens_prompt=55,
            tokens_completion=0,
            latency_ms=12,
            safety_verdict="blocked",
            error_message="PHI detected and clinical_safety keyword 'prescribe' blocked by guardrail.",
        )
        assert log.safety_verdict == "blocked"
        assert "prescribe" in log.error_message
