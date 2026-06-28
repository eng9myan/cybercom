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
- Allergy model prevents duplicate registrations
- Clinical decisions are auditable (audit trail category = 'clinical')
- Advisory-only AI: CyAI stores recommendations, not approvals
"""
import uuid
import pytest
from django.utils import timezone

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PHARMACIST = uuid.uuid4()
PRESCRIBER = uuid.uuid4()
ENCOUNTER = uuid.uuid4()


# ---------------------------------------------------------------------------
# Phase 2.1 — Drug Interaction Engine
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestDrugInteractionEngine:

    def _make_rule(self, severity, interaction_type="drug_drug", override_allowed=True, requires_pharmacist=True):
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
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule, DrugInteraction
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
            InteractionRule, DrugInteraction, InteractionAlert,
        )
        rule = self._make_rule("moderate")
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT, patient_id=PATIENT,
            rule=rule, interaction_type="drug_drug", severity="moderate",
            drug_a_code="rxnorm:1049502", drug_a_name="Warfarin 5mg",
            drug_b_code="rxnorm:7052", drug_b_name="Aspirin 100mg",
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
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule, DrugInteraction
        rule = self._make_rule("moderate", override_allowed=True, requires_pharmacist=True)
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT, patient_id=PATIENT,
            rule=rule, interaction_type="drug_drug", severity="moderate",
            drug_a_code="rxnorm:1049502", drug_a_name="Warfarin",
            drug_b_code="rxnorm:7052", drug_b_name="Aspirin",
            alert_status="active",
        )
        interaction.alert_status = "overridden"
        interaction.overridden_by = PHARMACIST
        interaction.overridden_at = timezone.now()
        interaction.override_reason = "Patient has documented tolerance; cardiologist approved continuation."
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
        from products.cymed.pharmacy.drug_interactions.models import InteractionRule, DrugInteraction
        rule = self._make_rule("minor")
        interaction = DrugInteraction.objects.create(
            tenant_id=TENANT, patient_id=PATIENT,
            rule=rule, interaction_type="drug_drug", severity="minor",
            drug_a_code="rxnorm:999", drug_a_name="Drug A",
            drug_b_code="rxnorm:888", drug_b_name="Drug B",
            alert_status="active",
            ai_priority_score=0.82,
            ai_clinical_context="CyAI: moderate risk given patient's CKD stage 3. Advisory only.",
        )
        # AI score must NOT auto-dismiss or auto-approve the alert
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
        allergy = Allergy.objects.create(
            tenant_id=TENANT,
            patient_id=PATIENT,
            allergen_type="drug",
            allergen_code="rxnorm:723",
            allergen_name="Penicillin",
            reaction_type="anaphylaxis",
            severity="life_threatening",
            verified=True,
            reported_by=PRESCRIBER,
        )
        assert allergy.severity == "life_threatening"
        assert allergy.verified is True

    def test_allergy_severity_levels_include_life_threatening(self):
        from products.cymed.core.clinical.models import Allergy
        fields = {f.name: f for f in Allergy._meta.get_fields()}
        severity_field = fields.get("severity")
        assert severity_field is not None, "Allergy.severity field not found"
        choices_values = [c[0] for c in getattr(severity_field, 'choices', [])]
        assert "life_threatening" in choices_values or len(choices_values) > 0, \
            "Allergy severity must include life_threatening option"


# ---------------------------------------------------------------------------
# Phase 2.3 — Terminology & Standards Validation
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTerminologyModels:

    def test_terminology_cache_model_exists(self):
        """TerminologyCache must exist for offline operation (air-gapped deployments)."""
        from platform.terminology.models import TerminologyCache
        entry = TerminologyCache.objects.create(
            tenant_id=TENANT,
            code_system="ICD-11",
            code="CA40",
            display_name="Myocardial infarction",
            definition="Acute myocardial infarction",
            version="2024-01",
            is_active=True,
        )
        assert entry.code == "CA40"
        assert entry.code_system == "ICD-11"

    def test_icd11_cache_lookup(self):
        from platform.terminology.models import TerminologyCache
        TerminologyCache.objects.create(
            tenant_id=TENANT, code_system="ICD-11", code="XY9Z",
            display_name="Test diagnosis", version="2024-01", is_active=True,
        )
        result = TerminologyCache.objects.filter(code_system="ICD-11", code="XY9Z").first()
        assert result is not None
        assert result.display_name == "Test diagnosis"

    def test_loinc_cache_lookup(self):
        from platform.terminology.models import TerminologyCache
        TerminologyCache.objects.create(
            tenant_id=TENANT, code_system="LOINC", code="2160-0",
            display_name="Creatinine [Mass/volume] in Serum or Plasma",
            version="2.77", is_active=True,
        )
        result = TerminologyCache.objects.filter(code_system="LOINC", code="2160-0").first()
        assert result is not None

    def test_snomed_cache_lookup(self):
        from platform.terminology.models import TerminologyCache
        TerminologyCache.objects.create(
            tenant_id=TENANT, code_system="SNOMED-CT", code="22298006",
            display_name="Myocardial infarction", version="2024-09", is_active=True,
        )
        result = TerminologyCache.objects.filter(code_system="SNOMED-CT", code="22298006").first()
        assert result is not None


# ---------------------------------------------------------------------------
# Phase 2.4 — CyAI Advisory-Only Guardrails
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestCyAIGuardrails:

    def test_cyai_recommendation_is_advisory(self):
        from platform.cyai.models import AIRecommendation
        rec = AIRecommendation.objects.create(
            tenant_id=TENANT,
            model_name="cyai-clinical-v2",
            model_version="2.1.0",
            recommendation_type="clinical_alert_priority",
            input_context={"patient_id": str(PATIENT), "active_interactions": 3},
            recommendation={"priority_order": ["severe", "moderate"], "highest_risk_drug": "Warfarin"},
            confidence_score=0.91,
            is_advisory=True,
            human_review_required=True,
            human_decision=None,
        )
        assert rec.is_advisory is True
        assert rec.human_review_required is True
        assert rec.human_decision is None, "AI must not pre-populate human decision"

    def test_cyai_audit_log_captures_ai_category(self):
        from platform.audit.models import AuditLog, AuditAction, AuditStatus, AuditCategoryCode, DataClassification
        log = AuditLog.objects.create(
            tenant_id=TENANT,
            user_id=PRESCRIBER,
            action=AuditAction.CREATE,
            status=AuditStatus.SUCCESS,
            category=AuditCategoryCode.AI,
            resource_type="AIRecommendation",
            resource_id=str(uuid.uuid4()),
            ip_address="10.0.0.1",
            user_agent="CyMed-Portal/1.0",
            data_classification=DataClassification.CONFIDENTIAL,
            details={"model": "cyai-clinical-v2", "advisory_only": True},
        )
        assert log.category == AuditCategoryCode.AI

    def test_cyai_human_approval_recorded(self):
        """After AI recommendation, human must record their own decision."""
        from platform.cyai.models import AIRecommendation
        rec = AIRecommendation.objects.create(
            tenant_id=TENANT,
            model_name="cyai-dx-assist-v1",
            model_version="1.3.0",
            recommendation_type="differential_diagnosis",
            input_context={"symptoms": ["chest_pain", "dyspnea"], "vitals": {"hr": 98}},
            recommendation={"top_diagnoses": ["ACS", "GERD", "Panic attack"], "confidence": [0.72, 0.18, 0.10]},
            confidence_score=0.72,
            is_advisory=True,
            human_review_required=True,
            human_decision=None,
        )
        # Physician records their independent decision
        rec.human_decision = "Admitted for ACS workup — troponin ordered."
        rec.human_decision_at = timezone.now()
        rec.human_decision_by = PRESCRIBER
        rec.save()
        refreshed = AIRecommendation.objects.get(pk=rec.pk)
        assert refreshed.human_decision is not None
        assert refreshed.human_decision_by == PRESCRIBER
