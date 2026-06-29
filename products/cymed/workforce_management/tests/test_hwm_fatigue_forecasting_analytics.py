"""
Tests for CyMed Workforce Management — Fatigue, Forecasting, Analytics modules.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from django.test import TestCase

TENANT = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
FACILITY = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
DEPT = uuid.UUID("cccccccc-0000-0000-0000-000000000001")
EMP_1 = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
EMP_2 = uuid.UUID("dddddddd-0000-0000-0000-000000000002")
SUPERVISOR = uuid.UUID("eeeeeeee-0000-0000-0000-000000000001")


def _mk(**kwargs):
    return {"tenant_id": TENANT, **kwargs}


# ---------------------------------------------------------------------------
# Fatigue & Duty Hours Tests
# ---------------------------------------------------------------------------


class DutyHourLogTest(TestCase):
    def test_duty_log_creation(self):
        from products.cymed.workforce_management.fatigue.models import DutyHourLog

        now = datetime.now(tz=UTC)
        log = DutyHourLog.objects.create(
            **_mk(
                workforce_profile_id=EMP_1,
                facility_id=FACILITY,
                clock_in=now,
                clock_out=now + timedelta(hours=12),
                hours_worked=12.0,
                is_resident=False,
                is_night_shift=False,
            )
        )
        self.assertEqual(log.hours_worked, 12.0)
        self.assertFalse(log.is_resident)

    def test_resident_duty_log(self):
        from products.cymed.workforce_management.fatigue.models import DutyHourLog

        now = datetime.now(tz=UTC)
        log = DutyHourLog.objects.create(
            **_mk(
                workforce_profile_id=EMP_2,
                facility_id=FACILITY,
                clock_in=now,
                clock_out=now + timedelta(hours=24),
                hours_worked=24.0,
                is_resident=True,
                includes_handover=True,
            )
        )
        self.assertTrue(log.is_resident)
        self.assertTrue(log.includes_handover)


class WeeklyHoursSummaryTest(TestCase):
    def test_weekly_summary_creation(self):
        from products.cymed.workforce_management.fatigue.models import WeeklyHoursSummary

        summary = WeeklyHoursSummary.objects.create(
            **_mk(
                workforce_profile_id=EMP_1,
                week_start=date(2026, 6, 29),
                total_hours=48.0,
                night_shift_count=2,
                consecutive_days_worked=5,
                is_resident=False,
            )
        )
        self.assertEqual(summary.total_hours, 48.0)
        self.assertEqual(summary.consecutive_days_worked, 5)

    def test_resident_acgme_tracking(self):
        from products.cymed.workforce_management.fatigue.models import WeeklyHoursSummary

        summary = WeeklyHoursSummary.objects.create(
            **_mk(
                workforce_profile_id=EMP_2,
                week_start=date(2026, 6, 29),
                total_hours=75.0,
                is_resident=True,
                rolling_4wk_avg_hours=72.5,
            )
        )
        self.assertTrue(summary.is_resident)
        self.assertEqual(summary.rolling_4wk_avg_hours, 72.5)

    def test_weekly_summary_unique_per_profile_week(self):
        from django.db import IntegrityError

        from products.cymed.workforce_management.fatigue.models import WeeklyHoursSummary

        WeeklyHoursSummary.objects.create(
            **_mk(
                workforce_profile_id=EMP_1,
                week_start=date(2026, 7, 6),
                total_hours=36.0,
            )
        )
        with self.assertRaises(IntegrityError):
            WeeklyHoursSummary.objects.create(
                **_mk(
                    workforce_profile_id=EMP_1,
                    week_start=date(2026, 7, 6),
                    total_hours=40.0,
                )
            )


class FatigueViolationTest(TestCase):
    def test_max_weekly_hours_violation(self):
        from products.cymed.workforce_management.fatigue.models import FatigueViolation

        v = FatigueViolation.objects.create(
            **_mk(
                workforce_profile_id=EMP_1,
                violation_type="max_weekly_hours",
                status="active",
            )
        )
        self.assertEqual(v.violation_type, "max_weekly_hours")
        self.assertEqual(v.status, "active")
        self.assertFalse(v.prescribing_authority_revoked)

    def test_acgme_28h_revokes_prescribing(self):
        from products.cymed.workforce_management.fatigue.models import FatigueViolation

        v = FatigueViolation.objects.create(
            **_mk(
                workforce_profile_id=EMP_2,
                violation_type="acgme_max_shift_28h",
                status="active",
                prescribing_authority_revoked=True,
            )
        )
        self.assertTrue(v.prescribing_authority_revoked)

    def test_violation_override(self):
        from products.cymed.workforce_management.fatigue.models import FatigueViolation

        v = FatigueViolation.objects.create(
            **_mk(
                workforce_profile_id=EMP_1,
                violation_type="max_consecutive_days",
                status="active",
            )
        )
        v.status = "overridden"
        v.override_by_id = SUPERVISOR
        v.override_reason = "Disaster surge — ICU census spike"
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.status, "overridden")
        self.assertEqual(v.override_by_id, SUPERVISOR)


class DisasterOverrideTest(TestCase):
    def test_disaster_override_creation(self):
        from products.cymed.workforce_management.fatigue.models import DisasterOverride

        override = DisasterOverride.objects.create(
            **_mk(
                authorized_by_id=SUPERVISOR,
                authorized_by_role="medical_director",
                incident_id="INC-2026-FLOOD-001",
                facility_id=FACILITY,
                override_reason="Regional flooding — mass casualty incident",
                is_active=True,
            )
        )
        self.assertTrue(override.is_active)
        self.assertEqual(override.incident_id, "INC-2026-FLOOD-001")

    def test_disaster_override_deactivation(self):
        from products.cymed.workforce_management.fatigue.models import DisasterOverride

        override = DisasterOverride.objects.create(
            **_mk(
                authorized_by_id=SUPERVISOR,
                authorized_by_role="medical_director",
                incident_id="INC-2026-FLOOD-001",
                facility_id=FACILITY,
                override_reason="Mass casualty",
                is_active=True,
            )
        )
        override.is_active = False
        override.deactivated_at = datetime.now(tz=UTC)
        override.save()
        override.refresh_from_db()
        self.assertFalse(override.is_active)
        self.assertIsNotNone(override.deactivated_at)


# ---------------------------------------------------------------------------
# Forecasting Tests
# ---------------------------------------------------------------------------


class CensusDataPointTest(TestCase):
    def test_census_data_point(self):
        from products.cymed.workforce_management.forecasting.models import CensusDataPoint

        dp = CensusDataPoint.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                census_date=date(2026, 7, 1),
                actual_census=42,
                source="inpatient_admissions",
            )
        )
        self.assertEqual(dp.actual_census, 42)
        self.assertEqual(dp.source, "inpatient_admissions")


class StaffingForecastTest(TestCase):
    def test_forecast_creation(self):
        from products.cymed.workforce_management.forecasting.models import StaffingForecast

        forecast = StaffingForecast.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                forecast_date=date(2026, 7, 15),
                model_version="cyai-staffing-v2.1",
                predicted_census=55,
                recommended_fte=18.5,
                recommended_nurse_fte=14.0,
                recommended_physician_fte=4.5,
                status="generated",
            )
        )
        self.assertEqual(forecast.predicted_census, 55)
        self.assertEqual(forecast.recommended_fte, 18.5)
        self.assertEqual(forecast.status, "generated")

    def test_surge_forecast(self):
        from products.cymed.workforce_management.forecasting.models import StaffingForecast

        forecast = StaffingForecast.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                forecast_date=date(2026, 1, 10),
                predicted_census=95,
                recommended_fte=32.0,
                surge_predicted=True,
                surge_reason="Influenza surge — winter season peak",
                status="generated",
            )
        )
        self.assertTrue(forecast.surge_predicted)
        self.assertIn("Influenza", forecast.surge_reason)

    def test_forecast_adjustment(self):
        from products.cymed.workforce_management.forecasting.models import (
            ForecastAdjustment,
            StaffingForecast,
        )

        forecast = StaffingForecast.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                forecast_date=date(2026, 7, 15),
                predicted_census=50,
                recommended_fte=16.0,
                status="generated",
            )
        )
        adjustment = ForecastAdjustment.objects.create(
            **_mk(
                forecast=forecast,
                adjusted_by_id=SUPERVISOR,
                original_fte=16.0,
                adjusted_fte=18.0,
                reason="Elective surgery backlog this week — added 2 FTE",
            )
        )
        self.assertEqual(adjustment.adjusted_fte, 18.0)

    def test_forecast_roster_mapping(self):
        from products.cymed.workforce_management.forecasting.models import (
            ForecastRosterMapping,
            StaffingForecast,
        )

        forecast = StaffingForecast.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                forecast_date=date(2026, 7, 15),
                predicted_census=50,
                recommended_fte=16.0,
                status="generated",
            )
        )
        ForecastRosterMapping.objects.create(
            **_mk(
                forecast=forecast,
                roster_cycle_id=uuid.uuid4(),
                applied_by_id=SUPERVISOR,
            )
        )
        self.assertEqual(forecast.roster_mappings.count(), 1)


# ---------------------------------------------------------------------------
# Analytics Tests
# ---------------------------------------------------------------------------


class WorkforceAnalyticsSnapshotTest(TestCase):
    def test_monthly_snapshot(self):
        from products.cymed.workforce_management.analytics.models import WorkforceAnalyticsSnapshot

        snap = WorkforceAnalyticsSnapshot.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                period_type="monthly",
                period_start=date(2026, 6, 1),
                period_end=date(2026, 6, 30),
                total_fte=45.0,
                avg_nurse_patient_ratio=4.2,
                coverage_compliance_pct=97.5,
                overtime_hours=120.0,
                agency_hours=48.0,
                float_deployments=8,
                vacancy_shifts=3,
                total_shifts=420,
                vacancy_rate_pct=0.71,
                fatigue_violations=2,
                shortage_alerts=1,
            )
        )
        self.assertEqual(snap.coverage_compliance_pct, 97.5)
        self.assertEqual(snap.vacancy_shifts, 3)
        self.assertEqual(snap.float_deployments, 8)

    def test_snapshot_unique_per_period(self):
        from django.db import IntegrityError

        from products.cymed.workforce_management.analytics.models import WorkforceAnalyticsSnapshot

        WorkforceAnalyticsSnapshot.objects.create(
            **_mk(
                facility_id=FACILITY,
                department_id=DEPT,
                period_type="monthly",
                period_start=date(2026, 5, 1),
                period_end=date(2026, 5, 31),
                total_fte=40.0,
                coverage_compliance_pct=95.0,
            )
        )
        with self.assertRaises(IntegrityError):
            WorkforceAnalyticsSnapshot.objects.create(
                **_mk(
                    facility_id=FACILITY,
                    department_id=DEPT,
                    period_type="monthly",
                    period_start=date(2026, 5, 1),
                    period_end=date(2026, 5, 31),
                    total_fte=42.0,
                    coverage_compliance_pct=96.0,
                )
            )


class WorkforceReportTest(TestCase):
    def test_fatigue_compliance_report(self):
        from products.cymed.workforce_management.analytics.models import WorkforceReport

        report = WorkforceReport.objects.create(
            **_mk(
                generated_by_id=SUPERVISOR,
                report_type="fatigue_compliance",
                facility_id=FACILITY,
                period_start=date(2026, 6, 1),
                period_end=date(2026, 6, 30),
                report_data={
                    "total_violations": 3,
                    "acgme_violations": 1,
                    "overrides_approved": 0,
                    "residents_flagged": ["EMP-001"],
                },
            )
        )
        self.assertEqual(report.report_type, "fatigue_compliance")
        self.assertEqual(report.report_data["total_violations"], 3)


class OnCallSLAMetricTest(TestCase):
    def test_sla_metric_creation(self):
        from products.cymed.workforce_management.analytics.models import OnCallSLAMetric

        metric = OnCallSLAMetric.objects.create(
            **_mk(
                facility_id=FACILITY,
                specialty="Cardiology",
                metric_date=date(2026, 6, 30),
                total_pages=24,
                pages_within_sla=22,
                pages_escalated=2,
                avg_response_minutes=8.5,
                sla_compliance_pct=91.67,
            )
        )
        self.assertEqual(metric.total_pages, 24)
        self.assertEqual(metric.pages_within_sla, 22)
        self.assertEqual(metric.sla_compliance_pct, 91.67)
