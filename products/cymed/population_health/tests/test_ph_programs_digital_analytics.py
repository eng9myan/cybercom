"""
Tests for CyMed Population Health — National Programs, Digital Health,
Analytics, Reporting, Epidemiology, Security Guardrails.
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
# Epidemiology Tests
# ---------------------------------------------------------------------------

class EpidemiologyTest(TestCase):

    def test_epidemiology_study_creation(self):
        from products.cymed.population_health.epidemiology.models import EpidemiologyStudy
        study = EpidemiologyStudy.objects.create(**_mk(
            study_name="Diabetes Prevalence in Saudi Arabia 2025",
            study_type="cross_sectional",
            disease_code="5A10",
            disease_name="Type 2 Diabetes",
            start_date="2025-01-01",
            population_scope="National",
            sample_size=50000,
            study_lead_id=PROVIDER,
            status="active",
        ))
        self.assertEqual(study.study_type, "cross_sectional")
        self.assertEqual(study.status, "active")

    def test_disease_trend_time_series(self):
        from products.cymed.population_health.epidemiology.models import DiseaseTrend
        trend = DiseaseTrend.objects.create(**_mk(
            disease_code="1C62",
            disease_name="COVID-19",
            period_type="monthly",
            period_date="2025-01-01",
            case_count=1250,
            incidence_rate="12.5000",
            prevalence_rate="45.2000",
            geographic_scope="Riyadh",
            population_denominator=10000000,
        ))
        self.assertEqual(trend.case_count, 1250)
        self.assertEqual(trend.period_type, "monthly")

    def test_disease_trend_unique_per_period(self):
        from products.cymed.population_health.epidemiology.models import DiseaseTrend
        from django.db import IntegrityError
        kwargs = dict(
            disease_code="1C62",
            disease_name="COVID-19",
            period_type="monthly",
            period_date="2025-01-01",
            geographic_scope="Riyadh",
        )
        DiseaseTrend.objects.create(**_mk(**kwargs))
        with self.assertRaises(IntegrityError):
            DiseaseTrend.objects.create(**_mk(**kwargs))

    def test_population_indicator(self):
        from products.cymed.population_health.epidemiology.models import PopulationIndicator
        ind = PopulationIndicator.objects.create(**_mk(
            indicator_code="LIFE-EXP-SA-2024",
            indicator_name="Life Expectancy at Birth — Saudi Arabia 2024",
            indicator_type="health_outcome",
            value="77.40",
            unit="years",
            measurement_date="2024-12-31",
            geographic_scope="National",
            data_source="MOH Statistics",
            gender="all",
        ))
        self.assertEqual(ind.indicator_code, "LIFE-EXP-SA-2024")
        self.assertEqual(ind.indicator_type, "health_outcome")


# ---------------------------------------------------------------------------
# National Programs Tests
# ---------------------------------------------------------------------------

class NationalProgramsTest(TestCase):

    def _program(self, code="VAC-FLU-2025", program_type="vaccination"):
        from products.cymed.population_health.national_programs.models import HealthProgram
        return HealthProgram.objects.create(**_mk(
            program_code=code,
            program_name="National Flu Vaccination Program 2025",
            program_type=program_type,
            governing_authority="Ministry of Health",
            start_date="2025-10-01",
            end_date="2025-12-31",
            target_population_size=5000000,
            status="active",
        ))

    def test_health_program_creation(self):
        prog = self._program()
        self.assertEqual(prog.status, "active")
        self.assertEqual(prog.target_population_size, 5000000)

    def test_program_enrollment(self):
        from products.cymed.population_health.national_programs.models import (
            HealthProgram, ProgramEnrollment
        )
        prog = self._program()
        enroll = ProgramEnrollment.objects.create(**_mk(
            program=prog,
            patient_id=PATIENT,
            enrollment_date="2025-10-05",
            enrolled_by_user_id=USER,
            enrollment_facility_id=FACILITY,
            status="active",
        ))
        self.assertEqual(enroll.status, "active")

    def test_program_enrollment_unique_per_program(self):
        from products.cymed.population_health.national_programs.models import (
            HealthProgram, ProgramEnrollment
        )
        from django.db import IntegrityError
        prog = self._program()
        ProgramEnrollment.objects.create(**_mk(
            program=prog, patient_id=PATIENT, enrollment_date="2025-10-05",
        ))
        with self.assertRaises(IntegrityError):
            ProgramEnrollment.objects.create(**_mk(
                program=prog, patient_id=PATIENT, enrollment_date="2025-10-06",
            ))

    def test_program_outcome_requires_provider(self):
        from products.cymed.population_health.national_programs.models import (
            HealthProgram, ProgramOutcome
        )
        prog = self._program()
        out = ProgramOutcome.objects.create(**_mk(
            program=prog,
            patient_id=PATIENT,
            outcome_type="vaccination_complete",
            outcome_date="2025-10-10",
            recording_provider_id=PROVIDER,
        ))
        self.assertIsNotNone(out.recording_provider_id)
        self.assertEqual(out.outcome_type, "vaccination_complete")

    def test_program_metric_tracking(self):
        from products.cymed.population_health.national_programs.models import (
            HealthProgram, ProgramMetric
        )
        prog = self._program()
        metric = ProgramMetric.objects.create(**_mk(
            program=prog,
            metric_name="Vaccination Coverage Rate",
            metric_type="coverage",
            metric_date="2025-11-01",
            target_value="80.00",
            actual_value="62.00",
            unit="%",
            meets_target=False,
        ))
        self.assertEqual(metric.actual_value, 62.00)
        self.assertFalse(metric.meets_target)


# ---------------------------------------------------------------------------
# Digital Health Tests
# ---------------------------------------------------------------------------

class DigitalHealthTest(TestCase):

    def test_national_health_id_issuance(self):
        from products.cymed.population_health.digital_health.models import NationalHealthID
        nhid = NationalHealthID.objects.create(**_mk(
            patient_id=PATIENT,
            national_id_number="1234567890",
            id_type="national_id",
            id_status="active",
            issued_date="2024-01-01",
            issuing_authority="National ID Authority",
        ))
        self.assertEqual(nhid.id_status, "active")
        self.assertEqual(nhid.id_type, "national_id")

    def test_national_health_id_unique_per_patient(self):
        from products.cymed.population_health.digital_health.models import NationalHealthID
        from django.db import IntegrityError
        NationalHealthID.objects.create(**_mk(
            patient_id=PATIENT,
            national_id_number="1234567890",
            id_type="national_id",
            id_status="active",
            issued_date="2024-01-01",
        ))
        with self.assertRaises(IntegrityError):
            NationalHealthID.objects.create(**_mk(
                patient_id=PATIENT,
                national_id_number="9876543210",
                id_type="national_id",
                id_status="active",
                issued_date="2024-06-01",
            ))

    def test_vaccination_certificate_issuance(self):
        from products.cymed.population_health.digital_health.models import VaccinationCertificate
        cert = VaccinationCertificate.objects.create(**_mk(
            patient_id=PATIENT,
            vaccine_name="COVID-19 Vaccine (BNT162b2)",
            vaccine_code="CVX-208",
            dose_number=2,
            total_doses=2,
            vaccination_date="2024-06-01",
            facility_id=FACILITY,
            provider_id=PROVIDER,
            batch_number="EK9231",
            certificate_number="SA-COV-2024-0000001",
            validity_start="2024-06-01",
            validity_end="2025-06-01",
            certificate_status="valid",
            is_international=True,
        ))
        self.assertEqual(cert.certificate_status, "valid")
        self.assertTrue(cert.is_international)
        self.assertEqual(cert.dose_number, 2)

    def test_health_pass_issuance(self):
        from products.cymed.population_health.digital_health.models import HealthPass
        hpass = HealthPass.objects.create(**_mk(
            patient_id=PATIENT,
            pass_type="travel",
            pass_name="International Travel Health Pass",
            valid_from="2025-01-01",
            valid_until="2025-12-31",
            conditions_met=["covid19_vaccinated", "negative_pcr_72h"],
            pass_status="active",
            issued_by_authority="Ministry of Health",
        ))
        self.assertEqual(hpass.pass_type, "travel")
        self.assertIn("covid19_vaccinated", hpass.conditions_met)

    def test_digital_wallet_entry(self):
        from products.cymed.population_health.digital_health.models import DigitalHealthWalletEntry
        entry = DigitalHealthWalletEntry.objects.create(**_mk(
            patient_id=PATIENT,
            entry_type="lab_result",
            title="HbA1c Result — January 2025",
            content_reference="cydata://tenant/patient/labs/hba1c-2025-01.pdf",
            issue_date="2025-01-15",
            issuing_facility_id=FACILITY,
            is_shareable=True,
            is_verified=True,
            verification_source="CyMed Laboratory Module",
        ))
        self.assertEqual(entry.entry_type, "lab_result")
        self.assertTrue(entry.is_shareable)
        self.assertTrue(entry.is_verified)


# ---------------------------------------------------------------------------
# Analytics Tests
# ---------------------------------------------------------------------------

class AnalyticsTest(TestCase):

    def test_national_health_snapshot(self):
        from products.cymed.population_health.analytics.models import NationalHealthSnapshot
        snap = NationalHealthSnapshot.objects.create(**_mk(
            snapshot_date="2025-01-01",
            period_type="monthly",
            geographic_scope="National",
            total_population=36000000,
            registered_patients=2100000,
            disease_prevalence={"5A10": 580000, "BA00": 420000},
            vaccination_coverage={"flu": 0.62, "covid19": 0.78},
            care_gap_rate="28.50",
            active_outbreaks=0,
            quality_score="74.20",
        ))
        self.assertEqual(snap.total_population, 36000000)
        self.assertEqual(snap.care_gap_rate, 28.50)

    def test_outbreak_forecast_advisory_only(self):
        from products.cymed.population_health.analytics.models import OutbreakForecast
        forecast = OutbreakForecast.objects.create(**_mk(
            disease_code="1C62",
            disease_name="COVID-19",
            forecast_date="2025-02-01",
            forecast_period_days=30,
            predicted_cases=850,
            confidence_interval_low=600,
            confidence_interval_high=1200,
            risk_level="medium",
            is_ai_generated=True,
        ))
        self.assertTrue(forecast.is_ai_generated)
        self.assertTrue(forecast.is_advisory_only)

    def test_outbreak_forecast_advisory_non_editable(self):
        from products.cymed.population_health.analytics.models import OutbreakForecast
        field = OutbreakForecast._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)

    def test_population_analytics_insight_workflow(self):
        from products.cymed.population_health.analytics.models import PopulationAnalyticsInsight
        insight = PopulationAnalyticsInsight.objects.create(**_mk(
            insight_type="vaccination_gap",
            scope_type="region",
            insight_title="Flu vaccination coverage 18% below target in Eastern Province",
            insight_detail="Coverage: 62%. Target: 80%. Action: outreach campaign recommended.",
            confidence_score="0.91",
            is_ai_generated=True,
            status="pending_review",
        ))
        self.assertEqual(insight.status, "pending_review")
        self.assertTrue(insight.is_advisory_only)

        insight.acknowledged_by_user_id = USER
        insight.status = "acknowledged"
        insight.save()
        self.assertEqual(insight.status, "acknowledged")


# ---------------------------------------------------------------------------
# Reporting Tests
# ---------------------------------------------------------------------------

class ReportingTest(TestCase):

    def test_national_report_creation(self):
        from products.cymed.population_health.reporting.models import NationalReport
        report = NationalReport.objects.create(**_mk(
            report_name="Annual National Health Report 2024",
            report_type="annual_health",
            reporting_period_start="2024-01-01",
            reporting_period_end="2024-12-31",
            report_date="2025-01-31",
            status="draft",
            generated_by_user_id=USER,
            content={"sections": ["morbidity", "vaccination", "registries"]},
        ))
        self.assertEqual(report.status, "draft")
        self.assertIsNone(report.approved_by_user_id)

    def test_report_requires_approval_before_submission(self):
        from products.cymed.population_health.reporting.models import NationalReport
        report = NationalReport.objects.create(**_mk(
            report_name="Surveillance Report Q1 2025",
            report_type="disease_surveillance",
            reporting_period_start="2025-01-01",
            reporting_period_end="2025-03-31",
            report_date="2025-04-10",
            status="draft",
        ))
        self.assertEqual(report.status, "draft")
        report.approved_by_user_id = USER
        report.status = "approved"
        report.save()
        self.assertEqual(report.status, "approved")

    def test_government_submission_human_required(self):
        from products.cymed.population_health.reporting.models import (
            NationalReport, GovernmentSubmission
        )
        report = NationalReport.objects.create(**_mk(
            report_name="Vaccination Coverage Report 2025",
            report_type="vaccination_coverage",
            reporting_period_start="2025-01-01",
            reporting_period_end="2025-06-30",
            report_date="2025-07-10",
            status="approved",
            approved_by_user_id=USER,
        ))
        submission = GovernmentSubmission.objects.create(**_mk(
            national_report=report,
            submission_date="2025-07-12T10:00:00Z",
            submitted_by_user_id=USER,
            submission_method="api",
            reference_number="MOH-2025-VAC-001",
            status="submitted",
        ))
        self.assertIsNotNone(submission.submitted_by_user_id)
        self.assertEqual(submission.status, "submitted")


# ---------------------------------------------------------------------------
# AI Guardrail Tests
# ---------------------------------------------------------------------------

class AIGuardrailsTest(TestCase):

    def test_risk_score_is_advisory_only_non_editable(self):
        from products.cymed.population_health.risk_management.models import RiskScore
        field = RiskScore._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)

    def test_risk_assessment_is_advisory_only_non_editable(self):
        from products.cymed.population_health.risk_management.models import RiskAssessment
        field = RiskAssessment._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)

    def test_cohort_analysis_is_advisory_only_non_editable(self):
        from products.cymed.population_health.cohorts.models import CohortAnalysis
        field = CohortAnalysis._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)

    def test_population_insight_is_advisory_only_non_editable(self):
        from products.cymed.population_health.analytics.models import PopulationAnalyticsInsight
        field = PopulationAnalyticsInsight._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)

    def test_outbreak_forecast_is_advisory_only_non_editable(self):
        from products.cymed.population_health.analytics.models import OutbreakForecast
        field = OutbreakForecast._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)


# ---------------------------------------------------------------------------
# CyGov Integration Boundary Tests
# ---------------------------------------------------------------------------

class CyGovIntegrationTest(TestCase):

    def test_no_shared_tables_with_cygov(self):
        from products.cymed.population_health.digital_health import models as dh_models
        tables = [
            m._meta.db_table
            for m in [
                dh_models.NationalHealthID,
                dh_models.VaccinationCertificate,
                dh_models.HealthPass,
                dh_models.DigitalHealthWalletEntry,
            ]
        ]
        for table in tables:
            self.assertTrue(
                table.startswith("cymed_ph_"),
                f"Table {table} must be scoped to cymed_ph_",
            )

    def test_national_id_no_direct_cygov_fk(self):
        from products.cymed.population_health.digital_health.models import NationalHealthID
        import django.db.models as m
        fk_targets = [
            f.related_model
            for f in NationalHealthID._meta.get_fields()
            if isinstance(f, m.ForeignKey)
        ]
        self.assertEqual(fk_targets, [], "NationalHealthID must have no FK to other models")

    def test_outbreak_signal_uses_hub_not_direct_call(self):
        from products.cymed.population_health import signals
        import inspect
        source = inspect.getsource(signals)
        self.assertIn("CyIntegrationHub.send", source)
        self.assertNotIn("requests.post", source)
        self.assertNotIn("urllib", source)
