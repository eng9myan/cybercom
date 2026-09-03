"""End-to-end provisioning test (SQLite via core.settings_test)."""

import uuid
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from products.cycom.accounting.models import Account
from products.cycom.access.models import Role
from platform.provisioning.models import (
    ApprovalPolicy,
    ApprovalTier,
    BlueprintStatus,
    CompanyBlueprint,
    CompanySize,
)
from platform.provisioning.services import ProvisioningService

TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")


class ProvisioningFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_packs")

    def _blueprint(self, size=CompanySize.MEDIUM, packs=None):
        return CompanyBlueprint.objects.create(
            tenant_id=TENANT,
            company_name="Amman Builders Co.",
            country_code="JO",
            industry_key="construction",
            size=size,
            business_ops=["manages_projects", "buys_products"],
            selected_department_packs=packs or [],
            companies=1,
            branches=1,
            projects=3,
        )

    def test_catalog_seeded(self):
        from platform.provisioning.models import CountryPack, DepartmentPack, IndustryTemplate
        self.assertTrue(CountryPack.objects.filter(code="JO").exists())
        self.assertGreaterEqual(DepartmentPack.objects.count(), 5)
        self.assertTrue(IndustryTemplate.objects.filter(key="construction").exists())

    def test_provision_generates_coa(self):
        bp = self._blueprint()
        ProvisioningService(bp).build()
        # JO base CoA (31) + construction extras (8) = 39 accounts, all tenant-scoped.
        accounts = Account.objects.filter(tenant_id=TENANT)
        self.assertEqual(accounts.count(), 39)
        # Construction-specific account present with correct parent linkage.
        wip = accounts.get(code="1160")
        self.assertEqual(wip.name, "Work In Progress (Projects)")
        self.assertEqual(wip.parent.code, "1100")

    def test_provision_generates_roles(self):
        bp = self._blueprint()
        ProvisioningService(bp).build()
        names = set(Role.objects.filter(tenant_id=TENANT).values_list("name", flat=True))
        # From department packs + industry defaults.
        self.assertIn("Finance Manager", names)
        self.assertIn("Procurement Manager", names)
        self.assertIn("Project Manager", names)
        self.assertIn("General Manager", names)
        self.assertIn("Quantity Surveyor", names)

    def test_approval_tiers_scale_with_size(self):
        # Medium = 1.0x -> PR top tier begins at 5,000.
        bp_med = self._blueprint(size=CompanySize.MEDIUM)
        ProvisioningService(bp_med).build()
        pr = ApprovalPolicy.objects.get(tenant_id=TENANT, document_type="purchase_request")
        top = pr.tiers.order_by("sequence").last()
        self.assertEqual(top.approver_role, "General Manager")
        self.assertEqual(top.threshold_min, Decimal("5000.00"))

    def test_idempotent(self):
        bp = self._blueprint()
        ProvisioningService(bp).build()
        first = Account.objects.filter(tenant_id=TENANT).count()
        ProvisioningService(bp).build()  # re-run
        self.assertEqual(Account.objects.filter(tenant_id=TENANT).count(), first)
        self.assertEqual(bp.status, BlueprintStatus.PROVISIONED)

    def test_summary_populated(self):
        bp = self._blueprint()
        ProvisioningService(bp).build()
        s = bp.summary
        self.assertEqual(s["localization"]["currency"], "JOD")
        self.assertIn("projects", s["department_packs"])
        self.assertIn("purchase_request", s["approval_policies"])
        self.assertTrue(s["import_templates"])

    def test_every_industry_provisions(self):
        """All 11 catalog industries must build cleanly (no missing packs)."""
        from platform.provisioning.models import IndustryTemplate

        keys = list(IndustryTemplate.objects.values_list("key", flat=True))
        self.assertGreaterEqual(len(keys), 11)
        for i, key in enumerate(keys):
            tenant = uuid.uuid4()
            bp = CompanyBlueprint.objects.create(
                tenant_id=tenant,
                company_name=f"Test {key} Co.",
                country_code="JO",
                industry_key=key,
                size=CompanySize.MEDIUM,
            )
            result = ProvisioningService(bp).build()
            self.assertEqual(result.status, BlueprintStatus.PROVISIONED, key)
            self.assertTrue(result.summary["enabled_modules"], key)
            self.assertTrue(result.summary["approval_policies"], key)
            self.assertGreater(Account.objects.filter(tenant_id=tenant).count(), 30, key)

    def test_retailgroup_includes_pos(self):
        """The CyShop concept: retail group must enable the POS module."""
        bp = CompanyBlueprint.objects.create(
            tenant_id=uuid.uuid4(),
            company_name="Retail Group Co.",
            country_code="JO",
            industry_key="retailgroup",
            size=CompanySize.LARGE,
        )
        result = ProvisioningService(bp).build()
        self.assertIn("pos", result.summary["enabled_modules"])
        self.assertIn("pos", result.summary["department_packs"])
        self.assertIn("pos_discount", result.summary["approval_policies"])


class AIProposalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_packs")

    def test_sweets_manufacturer_example(self):
        """The doctrine example: sweets factory + branches + online sales."""
        from platform.provisioning.proposal import propose

        result = propose(
            "We are a sweets manufacturer in Jordan. We have one factory, one "
            "central warehouse, 22 branches, online sales and delivery platforms."
        )
        self.assertTrue(result["matched"])
        self.assertEqual(result["industry_key"], "manufacturing")
        self.assertIn("pos", result["extra_department_packs"])
        self.assertTrue(result["rationale"])

    def test_construction_description(self):
        from platform.provisioning.proposal import propose

        result = propose("Construction contractor in Amman with 3 sites, subcontractors and tenders.")
        self.assertTrue(result["matched"])
        self.assertEqual(result["industry_key"], "construction")

    def test_ngo_description(self):
        from platform.provisioning.proposal import propose

        result = propose("A charity NGO managing donor grants and beneficiaries.")
        self.assertTrue(result["matched"])
        self.assertEqual(result["industry_key"], "nonprofit")

    def test_gibberish_degrades_gracefully(self):
        from platform.provisioning.proposal import propose

        result = propose("qwerty asdf zxcv lorem ipsum dolor")
        self.assertFalse(result["matched"])
        self.assertIn("message", result)
