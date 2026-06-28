"""
Tests for CyMed Population Health — Care Gaps, Risk Management, Cohorts, Quality modules.
"""
import uuid
from django.test import TestCase

TENANT = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
PATIENT = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
PROVIDER = uuid.UUID("cccccccc-0000-0000-0000-000000000001")
FACILITY = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
USER = uuid.UUID("eeeeeeee-0000-0000-0000-000000000001")


def _mk(**kwargs):
    return {"tenant_id": TENANT, **kwargs}


# ---------------------------------------------------------------------------
# Care Gap Tests
# ---------------------------------------------------------------------------

class CareGapTest(TestCase):

    def test_care_gap_creation(self):
        from products.cymed.population_health.care_gaps.models import CareGap
        gap = CareGap.objects.create(**_mk(
            patient_id=PATIENT,
            gap_type="screening",
            gap_description="Mammography overdue — last done 2 years ago",
            due_date="2025-03-01",
            status="open",
            priority="high",
            source="automated",
        ))
        self.assertEqual(gap.gap_type, "screening")
        self.assertEqual(gap.priority, "high")
        self.assertEqual(gap.status, "open")

    def test_care_gap_rule_creation(self):
        from products.cymed.population_health.care_gaps.models import CareGapRule
        rule = CareGapRule.objects.create(**_mk(
            rule_name="Annual HbA1c for Diabetics",
            rule_code="DM-HBA1C-ANNUAL",
            gap_type="lab_test",
            criteria={"has_condition": "diabetes", "last_hba1c_days_ago_gt": 365},
            recommendation="Order HbA1c lab test",
            frequency_days=365,
            applies_to_conditions=["5A10"],
            applies_to_gender="all",
            is_active=True,
        ))
        self.assertEqual(rule.rule_code, "DM-HBA1C-ANNUAL")
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.frequency_days, 365)

    def test_care_gap_recommendation_ai_generated(self):
        from products.cymed.population_health.care_gaps.models import CareGap, CareGapRecommendation
        gap = CareGap.objects.create(**_mk(
            patient_id=PATIENT,
            gap_type="vaccination",
            gap_description="Flu vaccination due",
            status="open",
            priority="medium",
        ))
        rec = CareGapRecommendation.objects.create(**_mk(
            care_gap=gap,
            recommendation_text="Schedule annual influenza vaccination",
            loinc_code="46110-7",
            service_type="vaccination",
            is_ai_generated=True,
        ))
        self.assertTrue(rec.is_ai_generated)

    def test_care_gap_resolution_by_human(self):
        from products.cymed.population_health.care_gaps.models import (
            CareGap, CareGapResolution
        )
        gap = CareGap.objects.create(**_mk(
            patient_id=PATIENT,
            gap_type="follow_up",
            gap_description="Post-discharge follow-up overdue",
            status="open",
            priority="critical",
        ))
        resolution = CareGapResolution.objects.create(**_mk(
            care_gap=gap,
            resolved_by_user_id=USER,
            resolution_date="2025-04-10",
            resolution_type="completed",
            resolution_notes="Patient attended follow-up visit",
        ))
        gap.status = "closed"
        gap.save()
        self.assertEqual(resolution.resolution_type, "completed")
        self.assertEqual(gap.status, "closed")

    def test_care_gap_rule_gender_filter(self):
        from products.cymed.population_health.care_gaps.models import CareGapRule
        rule = CareGapRule.objects.create(**_mk(
            rule_name="Cervical Screening for Women",
            rule_code="CERV-SCREEN-F",
            gap_type="screening",
            frequency_days=365,
            applies_to_gender="female",
            age_min=25,
            age_max=65,
        ))
        self.assertEqual(rule.applies_to_gender, "female")
        self.assertEqual(rule.age_min, 25)


# ---------------------------------------------------------------------------
# Risk Management Tests
# ---------------------------------------------------------------------------

class RiskManagementTest(TestCase):

    def test_risk_score_ai_advisory_only(self):
        from products.cymed.population_health.risk_management.models import RiskScore
        score = RiskScore.objects.create(**_mk(
            patient_id=PATIENT,
            risk_category="readmission",
            score="78.50",
            risk_level="high",
            score_date="2025-01-15",
            is_ai_generated=True,
        ))
        self.assertTrue(score.is_ai_generated)
        self.assertTrue(score.is_advisory_only)

    def test_risk_score_advisory_only_non_editable(self):
        from products.cymed.population_health.risk_management.models import RiskScore
        field = RiskScore._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)

    def test_risk_factor_linked_to_score(self):
        from products.cymed.population_health.risk_management.models import RiskScore, RiskFactor
        score = RiskScore.objects.create(**_mk(
            patient_id=PATIENT,
            risk_category="mortality",
            score="65.00",
            risk_level="high",
            score_date="2025-02-01",
        ))
        factor = RiskFactor.objects.create(**_mk(
            risk_score=score,
            factor_name="Previous MI",
            factor_type="clinical",
            factor_value="1",
            contribution_weight="35.00",
            icd11_code="BA80",
        ))
        self.assertEqual(float(factor.contribution_weight), 35.00)
        self.assertEqual(factor.factor_type, "clinical")

    def test_risk_category_thresholds(self):
        from products.cymed.population_health.risk_management.models import RiskCategory
        cat = RiskCategory.objects.create(**_mk(
            category_code="READMIT-30D",
            category_name="30-Day Readmission Risk",
            low_threshold="0",
            moderate_threshold="25",
            high_threshold="50",
            very_high_threshold="75",
            interventions=["care_manager_assignment", "discharge_checklist", "follow_up_call"],
        ))
        self.assertEqual(cat.category_code, "READMIT-30D")
        self.assertIn("care_manager_assignment", cat.interventions)

    def test_risk_assessment_requires_human_acknowledgement(self):
        from products.cymed.population_health.risk_management.models import RiskAssessment
        assessment = RiskAssessment.objects.create(**_mk(
            patient_id=PATIENT,
            assessment_type="automated",
            assessment_date="2025-01-20",
            overall_risk_level="very_high",
            overall_score="82.00",
            is_ai_generated=True,
            status="pending_review",
        ))
        self.assertEqual(assessment.status, "pending_review")
        self.assertIsNone(assessment.acknowledged_by_user_id)

        assessment.acknowledged_by_user_id = USER
        assessment.status = "acknowledged"
        assessment.save()
        self.assertEqual(assessment.status, "acknowledged")


# ---------------------------------------------------------------------------
# Cohort Tests
# ---------------------------------------------------------------------------

class CohortTest(TestCase):

    def test_cohort_creation(self):
        from products.cymed.population_health.cohorts.models import Cohort
        cohort = Cohort.objects.create(**_mk(
            name="High-Risk Diabetics 2025",
            cohort_type="quality",
            description="Diabetic patients with poor glycemic control",
            inclusion_criteria={"condition": "diabetes", "hba1c_gt": 9.0},
            exclusion_criteria={"age_lt": 18},
            created_by_user_id=USER,
            is_dynamic=True,
        ))
        self.assertEqual(cohort.cohort_type, "quality")
        self.assertTrue(cohort.is_dynamic)

    def test_cohort_member_unique_per_cohort(self):
        from products.cymed.population_health.cohorts.models import Cohort, CohortMember
        from django.db import IntegrityError
        cohort = Cohort.objects.create(**_mk(
            name="Test Cohort",
            cohort_type="study",
            created_by_user_id=USER,
        ))
        CohortMember.objects.create(**_mk(cohort=cohort, patient_id=PATIENT))
        with self.assertRaises(IntegrityError):
            CohortMember.objects.create(**_mk(cohort=cohort, patient_id=PATIENT))

    def test_cohort_outcome(self):
        from products.cymed.population_health.cohorts.models import Cohort, CohortOutcome
        cohort = Cohort.objects.create(**_mk(
            name="Hypertension Management",
            cohort_type="intervention",
            created_by_user_id=USER,
        ))
        out = CohortOutcome.objects.create(**_mk(
            cohort=cohort,
            patient_id=PATIENT,
            outcome_name="BP Controlled (<140/90)",
            outcome_type="clinical",
            measurement_date="2025-06-01",
            value="135/85",
            unit="mmHg",
        ))
        self.assertEqual(out.outcome_type, "clinical")

    def test_cohort_analysis_ai_advisory(self):
        from products.cymed.population_health.cohorts.models import Cohort, CohortAnalysis
        cohort = Cohort.objects.create(**_mk(
            name="Cancer Screening Cohort",
            cohort_type="registry",
            created_by_user_id=USER,
        ))
        analysis = CohortAnalysis.objects.create(**_mk(
            cohort=cohort,
            analysis_type="outcome",
            analysis_name="5-Year Survival Analysis",
            analysis_date="2025-01-01",
            results={"5yr_survival_rate": 0.78, "n": 450},
            is_ai_generated=True,
        ))
        self.assertTrue(analysis.is_ai_generated)
        self.assertTrue(analysis.is_advisory_only)


# ---------------------------------------------------------------------------
# Quality Tests
# ---------------------------------------------------------------------------

class QualityTest(TestCase):

    def test_quality_measure_definition(self):
        from products.cymed.population_health.quality.models import QualityMeasure
        measure = QualityMeasure.objects.create(**_mk(
            measure_code="HBA1C-CONTROL",
            measure_name="HbA1c Control in Diabetic Patients",
            measure_type="outcome",
            target_percentage="80.00",
            benchmark_percentage="75.00",
            is_national=True,
            reporting_period="annual",
        ))
        self.assertEqual(measure.measure_code, "HBA1C-CONTROL")
        self.assertTrue(measure.is_national)
        self.assertEqual(measure.reporting_period, "annual")

    def test_quality_measure_result_calculation(self):
        from products.cymed.population_health.quality.models import QualityMeasure, QualityMeasureResult
        measure = QualityMeasure.objects.create(**_mk(
            measure_code="MAMMO-SCREEN",
            measure_name="Mammography Screening Rate",
            measure_type="process",
        ))
        result = QualityMeasureResult.objects.create(**_mk(
            measure=measure,
            facility_id=FACILITY,
            period_start="2024-01-01",
            period_end="2024-12-31",
            numerator=720,
            denominator=1000,
            performance_rate="72.00",
            benchmark_rate="80.00",
            meets_target=False,
        ))
        self.assertEqual(result.numerator, 720)
        self.assertFalse(result.meets_target)

    def test_quality_improvement_plan(self):
        from products.cymed.population_health.quality.models import (
            QualityMeasure, QualityMeasureResult, QualityImprovement
        )
        measure = QualityMeasure.objects.create(**_mk(
            measure_code="FLU-VAC-RATE",
            measure_name="Influenza Vaccination Rate",
            measure_type="process",
        ))
        result = QualityMeasureResult.objects.create(**_mk(
            measure=measure,
            facility_id=FACILITY,
            period_start="2024-01-01",
            period_end="2024-12-31",
            numerator=300,
            denominator=600,
            performance_rate="50.00",
            meets_target=False,
        ))
        improvement = QualityImprovement.objects.create(**_mk(
            measure_result=result,
            intervention_type="care_pathway",
            intervention_description="Embed flu vaccine order in annual wellness visit pathway",
            start_date="2025-01-01",
            status="active",
            expected_improvement="20.00",
            responsible_user_id=USER,
        ))
        self.assertEqual(improvement.status, "active")
        self.assertEqual(improvement.intervention_type, "care_pathway")

    def test_clinical_audit(self):
        from products.cymed.population_health.quality.models import ClinicalAudit
        audit = ClinicalAudit.objects.create(**_mk(
            audit_name="Antibiotic Stewardship Audit Q1 2025",
            audit_type="medication",
            facility_id=FACILITY,
            period_start="2025-01-01",
            period_end="2025-03-31",
            audit_criteria=["indication_documented", "duration_appropriate", "culture_obtained"],
            auditor_id=USER,
            status="in_progress",
            sample_size=100,
            compliant_count=72,
            compliance_rate="72.00",
        ))
        self.assertEqual(float(audit.compliance_rate), 72.00)
        self.assertEqual(audit.audit_type, "medication")

    def test_quality_measure_unique_result_per_period(self):
        from products.cymed.population_health.quality.models import QualityMeasure, QualityMeasureResult
        from django.db import IntegrityError
        measure = QualityMeasure.objects.create(**_mk(
            measure_code="READMIT-30D",
            measure_name="30-Day Readmission Rate",
            measure_type="outcome",
        ))
        QualityMeasureResult.objects.create(**_mk(
            measure=measure,
            facility_id=FACILITY,
            period_start="2024-01-01",
            period_end="2024-12-31",
            numerator=45,
            denominator=500,
            performance_rate="9.00",
        ))
        with self.assertRaises(IntegrityError):
            QualityMeasureResult.objects.create(**_mk(
                measure=measure,
                facility_id=FACILITY,
                period_start="2024-01-01",
                period_end="2024-12-31",
                numerator=47,
                denominator=500,
                performance_rate="9.40",
            ))
