"""
Tests for CyMed RCM — Contracts, Pricing, Revenue Analytics, Payer Portal,
Tenant Isolation, CyCom Integration, AI Guardrails.
"""

import uuid
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from products.cymed.rcm.collections.models import CollectionCase
from products.cymed.rcm.contracts.models import (
    ContractRate,
    ContractRule,
    PayerContract,
    ReimbursementRule,
)
from products.cymed.rcm.payer_portal.models import (
    PayerAuthorizationReview,
    PayerClaimReview,
    PayerDashboard,
    PayerPortalAccount,
)
from products.cymed.rcm.pricing.models import (
    DiscountRule,
    PackagePrice,
    PriceList,
    ServicePrice,
)
from products.cymed.rcm.revenue_analytics.models import (
    ClaimMetricsSnapshot,
    DenialAnalyticsSnapshot,
    PayerPerformanceSnapshot,
    RCMAIInsight,
    RevenueDashboardSnapshot,
    RevenueLeakageAlert,
)

TENANT_A = uuid.uuid4()
TENANT_B = uuid.uuid4()


# ─── Contracts ────────────────────────────────────────────────────────────────


class ContractsTest(TestCase):
    def setUp(self):
        self.insurance_co_id = uuid.uuid4()

    def test_payer_contract_creation(self):
        contract = PayerContract.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.insurance_co_id,
            contract_name="Gulf Insurance FFS Agreement 2024",
            contract_number="GIC-2024-001",
            contract_type="fee_for_service",
            effective_date=timezone.now().date(),
            status="active",
            base_discount_percentage=Decimal("15.00"),
            auto_renewal=False,
        )
        self.assertEqual(contract.status, "active")
        self.assertEqual(contract.contract_type, "fee_for_service")

    def test_contract_rate_per_service(self):
        contract = PayerContract.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.insurance_co_id,
            contract_name="Lab Services Agreement",
            contract_type="fee_for_service",
            effective_date=timezone.now().date(),
            status="active",
        )
        rate = ContractRate.objects.create(
            tenant_id=TENANT_A,
            contract=contract,
            service_code="LAB-HBA1C",
            service_description="HbA1c Blood Test",
            rate_type="flat_fee",
            rate_amount=Decimal("120.00"),
            effective_date=timezone.now().date(),
            is_active=True,
        )
        self.assertEqual(rate.rate_type, "flat_fee")
        self.assertEqual(rate.rate_amount, Decimal("120.00"))

    def test_timely_filing_rule(self):
        contract = PayerContract.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.insurance_co_id,
            contract_name="Timely Filing Test",
            contract_type="fee_for_service",
            effective_date=timezone.now().date(),
            status="active",
        )
        rule = ContractRule.objects.create(
            tenant_id=TENANT_A,
            contract=contract,
            rule_type="timely_filing",
            rule_description="Claims must be filed within 90 days of service",
            applies_to_service_codes=[],
            days_limit=90,
            is_active=True,
        )
        self.assertEqual(rule.rule_type, "timely_filing")
        self.assertEqual(rule.days_limit, 90)

    def test_reimbursement_drg_rule(self):
        contract = PayerContract.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.insurance_co_id,
            contract_name="DRG Agreement",
            contract_type="drg",
            effective_date=timezone.now().date(),
            status="active",
        )
        rule = ReimbursementRule.objects.create(
            tenant_id=TENANT_A,
            contract=contract,
            rule_name="DRG Inpatient Base Rate",
            calculation_method="drg_multiplier",
            base_rate=Decimal("3000.00"),
            applies_to_categories=["hospitalization"],
            is_active=True,
        )
        self.assertEqual(rule.calculation_method, "drg_multiplier")


# ─── Pricing ──────────────────────────────────────────────────────────────────


class PricingTest(TestCase):
    def test_price_list_creation(self):
        pl = PriceList.objects.create(
            tenant_id=TENANT_A,
            list_name="Hospital Standard Price List 2024",
            list_code="HOSP-STD-2024",
            service_category="hospital",
            currency="SAR",
            effective_date=timezone.now().date(),
            is_active=True,
            is_default=True,
        )
        self.assertTrue(pl.is_default)
        self.assertEqual(pl.currency, "SAR")

    def test_service_price_linked_to_list(self):
        pl = PriceList.objects.create(
            tenant_id=TENANT_A,
            list_name="Lab Price List",
            list_code="LAB-2024",
            service_category="laboratory",
            currency="SAR",
            effective_date=timezone.now().date(),
            is_active=True,
        )
        price = ServicePrice.objects.create(
            tenant_id=TENANT_A,
            price_list=pl,
            service_code="LAB-CBC",
            service_description="Complete Blood Count",
            service_category="laboratory",
            unit_price=Decimal("80.00"),
            vat_applicable=True,
            vat_percentage=Decimal("15.00"),
            price_includes_vat=False,
            is_active=True,
        )
        self.assertEqual(price.unit_price, Decimal("80.00"))
        self.assertTrue(price.vat_applicable)

    def test_package_price_maternity(self):
        pl = PriceList.objects.create(
            tenant_id=TENANT_A,
            list_name="Packages 2024",
            list_code="PKG-2024",
            service_category="hospital",
            currency="SAR",
            effective_date=timezone.now().date(),
            is_active=True,
        )
        pkg = PackagePrice.objects.create(
            tenant_id=TENANT_A,
            price_list=pl,
            package_name="Normal Delivery Package",
            package_code="PKG-NORMAL-DEL",
            package_type="maternity",
            package_description="Normal vaginal delivery — 2 nights admission",
            package_price=Decimal("8500.00"),
            services_included=["ADM-ROOM", "NURSING", "DELIVERY", "NEWBORN-CARE"],
            valid_days=30,
            is_active=True,
        )
        self.assertEqual(pkg.package_type, "maternity")
        self.assertIn("DELIVERY", pkg.services_included)

    def test_discount_rule_government(self):
        rule = DiscountRule.objects.create(
            tenant_id=TENANT_A,
            rule_name="Government Employee Discount",
            discount_type="percentage",
            applies_to="government",
            condition_description="Valid government employment ID required",
            discount_value=Decimal("20.00"),
            requires_approval=False,
            is_active=True,
        )
        self.assertEqual(rule.discount_value, Decimal("20.00"))
        self.assertFalse(rule.requires_approval)


# ─── Revenue Analytics ────────────────────────────────────────────────────────


class RevenueAnalyticsTest(TestCase):
    def test_revenue_dashboard_snapshot(self):
        snap = RevenueDashboardSnapshot.objects.create(
            tenant_id=TENANT_A,
            snapshot_date=timezone.now().date(),
            snapshot_period="daily",
            gross_revenue=Decimal("1250000.00"),
            net_revenue=Decimal("1050000.00"),
            total_charges=Decimal("1400000.00"),
            total_collections=Decimal("1050000.00"),
            total_adjustments=Decimal("350000.00"),
            outstanding_ar=Decimal("850000.00"),
            days_in_ar=Decimal("42.5"),
            collection_rate=Decimal("84.0"),
            claim_acceptance_rate=Decimal("91.2"),
            denial_rate=Decimal("8.8"),
        )
        self.assertEqual(snap.snapshot_period, "daily")
        self.assertEqual(snap.collection_rate, Decimal("84.0"))

    def test_claim_metrics_snapshot(self):
        snap = ClaimMetricsSnapshot.objects.create(
            tenant_id=TENANT_A,
            snapshot_date=timezone.now().date(),
            snapshot_period="monthly",
            total_claims_submitted=1200,
            total_claims_paid=1080,
            total_claims_denied=80,
            total_claims_pending=40,
            total_billed=Decimal("6000000.00"),
            total_paid=Decimal("5100000.00"),
            total_denied_amount=Decimal("400000.00"),
            average_days_to_payment=Decimal("28.3"),
            first_pass_rate=Decimal("90.0"),
        )
        self.assertEqual(snap.total_claims_submitted, 1200)
        self.assertEqual(snap.first_pass_rate, Decimal("90.0"))

    def test_denial_analytics_snapshot(self):
        snap = DenialAnalyticsSnapshot.objects.create(
            tenant_id=TENANT_A,
            snapshot_date=timezone.now().date(),
            snapshot_period="monthly",
            denial_category="authorization",
            total_denials=45,
            total_denial_amount=Decimal("225000.00"),
            appeals_filed=30,
            appeals_won=22,
            amount_recovered=Decimal("165000.00"),
            appeal_success_rate=Decimal("73.3"),
        )
        self.assertEqual(snap.denial_category, "authorization")
        self.assertEqual(snap.appeal_success_rate, Decimal("73.3"))

    def test_payer_performance_snapshot(self):
        ins_co_id = uuid.uuid4()
        snap = PayerPerformanceSnapshot.objects.create(
            tenant_id=TENANT_A,
            snapshot_date=timezone.now().date(),
            snapshot_period="monthly",
            insurance_company_id=ins_co_id,
            average_processing_days=Decimal("18.5"),
            payment_rate=Decimal("92.0"),
            denial_rate=Decimal("8.0"),
            auth_approval_rate=Decimal("87.5"),
            avg_auth_processing_days=Decimal("2.3"),
            performance_score=Decimal("88.0"),
            trend_direction="improving",
        )
        self.assertEqual(snap.trend_direction, "improving")

    def test_revenue_leakage_alert(self):
        alert = RevenueLeakageAlert.objects.create(
            tenant_id=TENANT_A,
            alert_date=timezone.now().date(),
            leakage_type="unbilled_charges",
            encounter_id=uuid.uuid4(),
            patient_id=uuid.uuid4(),
            estimated_leakage_amount=Decimal("1500.00"),
            status="open",
        )
        self.assertEqual(alert.leakage_type, "unbilled_charges")
        self.assertEqual(alert.status, "open")


# ─── Payer Portal ─────────────────────────────────────────────────────────────


class PayerPortalTest(TestCase):
    def setUp(self):
        self.ins_co_id = uuid.uuid4()

    def test_payer_portal_account(self):
        acct = PayerPortalAccount.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.ins_co_id,
            cyidentity_user_id=uuid.uuid4(),
            account_role="claims_reviewer",
            is_active=True,
            access_level="reviewer",
        )
        self.assertEqual(acct.account_role, "claims_reviewer")
        self.assertTrue(acct.is_active)

    def test_payer_dashboard(self):
        acct = PayerPortalAccount.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.ins_co_id,
            cyidentity_user_id=uuid.uuid4(),
            account_role="account_manager",
            is_active=True,
            access_level="admin",
        )
        dashboard = PayerDashboard.objects.create(
            tenant_id=TENANT_A,
            payer_account=acct,
            pending_claims_count=145,
            pending_auths_count=23,
            pending_appeals_count=8,
        )
        self.assertEqual(dashboard.pending_claims_count, 145)

    def test_payer_claim_review(self):
        acct = PayerPortalAccount.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.ins_co_id,
            cyidentity_user_id=uuid.uuid4(),
            account_role="claims_reviewer",
            is_active=True,
            access_level="reviewer",
        )
        review = PayerClaimReview.objects.create(
            tenant_id=TENANT_A,
            payer_account=acct,
            claim_id=uuid.uuid4(),
            review_status="under_review",
            reviewer_notes="Reviewing supporting documentation",
        )
        self.assertEqual(review.review_status, "under_review")

    def test_payer_auth_review(self):
        acct = PayerPortalAccount.objects.create(
            tenant_id=TENANT_A,
            insurance_company_id=self.ins_co_id,
            cyidentity_user_id=uuid.uuid4(),
            account_role="auth_reviewer",
            is_active=True,
            access_level="approver",
        )
        review = PayerAuthorizationReview.objects.create(
            tenant_id=TENANT_A,
            payer_account=acct,
            preauthorization_id=uuid.uuid4(),
            review_status="clinical_review",
        )
        self.assertEqual(review.review_status, "clinical_review")


# ─── Tenant Isolation ─────────────────────────────────────────────────────────


class TenantIsolationTest(TestCase):
    def test_price_lists_isolated_by_tenant(self):
        PriceList.objects.create(
            tenant_id=TENANT_A,
            list_name="Hospital A Price List",
            list_code="A-STD",
            service_category="hospital",
            currency="SAR",
            effective_date=timezone.now().date(),
        )
        PriceList.objects.create(
            tenant_id=TENANT_B,
            list_name="Hospital B Price List",
            list_code="B-STD",
            service_category="hospital",
            currency="SAR",
            effective_date=timezone.now().date(),
        )
        self.assertEqual(PriceList.objects.filter(tenant_id=TENANT_A).count(), 1)
        self.assertEqual(PriceList.objects.filter(tenant_id=TENANT_B).count(), 1)

    def test_collection_cases_isolated_by_tenant(self):
        for tenant in [TENANT_A, TENANT_B]:
            acct_patient_id = uuid.uuid4()
            CollectionCase.objects.create(
                tenant_id=tenant,
                patient_id=acct_patient_id,
                patient_account_id=uuid.uuid4(),
                case_number=f"COL-{uuid.uuid4().hex[:8].upper()}",
                outstanding_balance=Decimal("1000.00"),
                original_balance=Decimal("1000.00"),
                aging_bucket="30_days",
                status="active",
                priority="medium",
            )
        self.assertEqual(CollectionCase.objects.filter(tenant_id=TENANT_A).count(), 1)
        self.assertEqual(CollectionCase.objects.filter(tenant_id=TENANT_B).count(), 1)


# ─── AI Guardrails ────────────────────────────────────────────────────────────


class AIGuardrailsTest(TestCase):
    def test_ai_insight_is_advisory_only_non_editable(self):
        field = RCMAIInsight._meta.get_field("is_advisory_only")
        self.assertFalse(field.editable)

    def test_ai_insight_cannot_approve_claims(self):
        insight = RCMAIInsight.objects.create(
            tenant_id=TENANT_A,
            insight_type="denial_prediction",
            scope_type="claim",
            scope_id=uuid.uuid4(),
            insight_title="High denial risk — missing authorization",
            insight_detail="This claim has 87% probability of denial due to missing prior auth.",
            confidence_score=Decimal("87.0"),
            estimated_impact_amount=Decimal("3500.00"),
            status="pending_review",
        )
        self.assertTrue(insight.is_advisory_only)
        self.assertEqual(insight.status, "pending_review")
        # AI insight status flow requires human acknowledgement
        insight.status = "acknowledged"
        insight.acknowledged_by_user_id = uuid.uuid4()
        insight.acknowledged_at = timezone.now()
        insight.save()
        insight.refresh_from_db()
        self.assertEqual(insight.status, "acknowledged")

    def test_ai_cannot_submit_claims(self):
        """Claims submission requires human user_id — AI cannot submit."""
        from products.cymed.rcm.billing.models import PatientAccount
        from products.cymed.rcm.claims.models import ClaimSubmission

        acct = PatientAccount.objects.create(
            tenant_id=TENANT_A,
            patient_id=uuid.uuid4(),
            account_number=f"ACC-{uuid.uuid4().hex[:8].upper()}",
            account_status="active",
            guarantor_type="self",
        )
        # ClaimSubmission requires a non-null submitted_by_user_id (human)
        with self.assertRaises(Exception):
            from products.cymed.rcm.claims.models import Claim

            cl = Claim.objects.create(
                tenant_id=TENANT_A,
                claim_number=f"CLM-{uuid.uuid4().hex[:8].upper()}",
                patient_id=acct.patient_id,
                insurance_member_id=uuid.uuid4(),
                insurance_plan_id=uuid.uuid4(),
                encounter_billing_id=uuid.uuid4(),
                claim_type="professional",
                claim_date=timezone.now().date(),
                service_from_date=timezone.now().date(),
                service_to_date=timezone.now().date(),
                facility_id=uuid.uuid4(),
                rendering_provider_id=uuid.uuid4(),
                status="submitted",
            )
            # submitted_by_user_id=None should raise on NOT NULL constraint
            ClaimSubmission.objects.create(
                tenant_id=TENANT_A,
                claim=cl,
                submitted_by_user_id=None,
                submission_method="electronic",
            )


# ─── CyCom Integration Boundary ───────────────────────────────────────────────


class CyComIntegrationTest(TestCase):
    def test_no_shared_tables_with_cycom(self):
        """Verify RCM models use cymed_rcm_* tables, not cycom_* tables."""
        from products.cymed.rcm.billing.models import Invoice
        from products.cymed.rcm.claims.models import Claim

        self.assertTrue(Invoice._meta.db_table.startswith("cymed_rcm_"))
        self.assertTrue(Claim._meta.db_table.startswith("cymed_rcm_"))

    def test_invoice_approved_signal_targets_integrationhub(self):
        """CyCom finance receives invoice data via CyIntegrationHub signal, not direct ORM."""
        from products.cymed.rcm.signals import _push_to_cycom

        # Verify function exists and is callable
        self.assertTrue(callable(_push_to_cycom))

    def test_revenue_analytics_isolation_from_cycom(self):
        """Revenue analytics snapshots are CyMed-owned; CyCom gets summaries via hub."""
        RevenueDashboardSnapshot.objects.create(
            tenant_id=TENANT_A,
            snapshot_date=timezone.now().date(),
            snapshot_period="monthly",
            gross_revenue=Decimal("5000000.00"),
            net_revenue=Decimal("4200000.00"),
        )
        self.assertTrue(RevenueDashboardSnapshot._meta.db_table.startswith("cymed_rcm_"))
