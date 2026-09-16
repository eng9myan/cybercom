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

    def test_approval_override_disables_policy(self):
        bp = self._blueprint()
        bp.approval_overrides = {"payment": {"enabled": False}}
        bp.save()
        ProvisioningService(bp).build()
        policy = ApprovalPolicy.objects.get(tenant_id=TENANT, document_type="payment")
        self.assertFalse(policy.is_active)
        self.assertEqual(policy.tiers.count(), 0)
        # purchase_request had no override — untouched, still active.
        pr = ApprovalPolicy.objects.get(tenant_id=TENANT, document_type="purchase_request")
        self.assertTrue(pr.is_active)
        self.assertGreater(pr.tiers.count(), 0)

    def test_approval_override_custom_tiers_used_verbatim(self):
        # Custom tiers are the customer's final numbers — no size multiplier
        # applied, unlike the template-derived default path.
        bp = self._blueprint(size=CompanySize.ENTERPRISE)  # 10x multiplier
        bp.approval_overrides = {
            "purchase_request": {
                "enabled": True,
                "tiers": [
                    {"min": 0, "max": 1000, "role": "Site Supervisor"},
                    {"min": 1000, "max": None, "role": "CFO"},
                ],
            }
        }
        bp.save()
        ProvisioningService(bp).build()
        pr = ApprovalPolicy.objects.get(tenant_id=TENANT, document_type="purchase_request")
        tiers = list(pr.tiers.order_by("sequence"))
        self.assertEqual(len(tiers), 2)
        self.assertEqual(tiers[0].threshold_max, Decimal("1000"))
        self.assertEqual(tiers[0].approver_role, "Site Supervisor")
        self.assertIsNone(tiers[1].threshold_max)
        self.assertEqual(tiers[1].approver_role, "CFO")

    def test_approval_override_reenable_on_reprovision(self):
        bp = self._blueprint()
        bp.approval_overrides = {"payment": {"enabled": False}}
        bp.save()
        ProvisioningService(bp).build()
        bp.approval_overrides = {}
        bp.save()
        ProvisioningService(bp).build()
        policy = ApprovalPolicy.objects.get(tenant_id=TENANT, document_type="payment")
        self.assertTrue(policy.is_active)
        self.assertGreater(policy.tiers.count(), 0)

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
        self.assertGreaterEqual(len(keys), 17)
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

    def test_retail_grocery(self):
        bp = CompanyBlueprint.objects.create(
            tenant_id=uuid.uuid4(), company_name="Corner Grocery Co.",
            country_code="JO", industry_key="retail_grocery", size=CompanySize.SMALL,
        )
        result = ProvisioningService(bp).build()
        self.assertIn("pos", result.summary["enabled_modules"])
        self.assertIn("pos_discount", result.summary["approval_policies"])
        self.assertTrue(Role.objects.filter(tenant_id=bp.tenant_id, name="Store Manager").exists())
        self.assertTrue(Account.objects.filter(tenant_id=bp.tenant_id, code="4130", name="Grocery POS Revenue").exists())

    def test_retail_fastfood(self):
        bp = CompanyBlueprint.objects.create(
            tenant_id=uuid.uuid4(), company_name="Quick Burger Co.",
            country_code="JO", industry_key="retail_fastfood", size=CompanySize.SMALL,
        )
        result = ProvisioningService(bp).build()
        self.assertIn("pos", result.summary["enabled_modules"])
        self.assertTrue(Role.objects.filter(tenant_id=bp.tenant_id, name="Shift Manager").exists())
        self.assertTrue(Account.objects.filter(tenant_id=bp.tenant_id, code="4130", name="Fast Food POS Revenue").exists())

    def test_retail_fastfood_tables(self):
        bp = CompanyBlueprint.objects.create(
            tenant_id=uuid.uuid4(), company_name="Sit-Down Burger Co.",
            country_code="JO", industry_key="retail_fastfood_tables", size=CompanySize.SMALL,
        )
        result = ProvisioningService(bp).build()
        self.assertIn("pos", result.summary["enabled_modules"])
        self.assertTrue(Role.objects.filter(tenant_id=bp.tenant_id, name="Shift Manager").exists())

    def test_retail_restaurant(self):
        bp = CompanyBlueprint.objects.create(
            tenant_id=uuid.uuid4(), company_name="Amman Bistro Co.",
            country_code="JO", industry_key="retail_restaurant", size=CompanySize.MEDIUM,
        )
        result = ProvisioningService(bp).build()
        self.assertIn("pos", result.summary["enabled_modules"])
        self.assertIn("pos_comp", result.summary["approval_policies"])
        names = set(Role.objects.filter(tenant_id=bp.tenant_id).values_list("name", flat=True))
        self.assertIn("Waiter", names)
        self.assertIn("Head Waiter", names)
        self.assertIn("Kitchen Manager", names)

    def test_retail_autoparts(self):
        bp = CompanyBlueprint.objects.create(
            tenant_id=uuid.uuid4(), company_name="Amman Auto Parts Co.",
            country_code="JO", industry_key="retail_autoparts", size=CompanySize.MEDIUM,
        )
        result = ProvisioningService(bp).build()
        self.assertIn("pos", result.summary["department_packs"])
        self.assertIn("sales", result.summary["department_packs"])
        self.assertTrue(Account.objects.filter(tenant_id=bp.tenant_id, code="2115", name="Core Charge Liability", account_type="liability").exists())

    def test_retail_pharmacy(self):
        bp = CompanyBlueprint.objects.create(
            tenant_id=uuid.uuid4(), company_name="Amman Pharmacy Co.",
            country_code="JO", industry_key="retail_pharmacy", size=CompanySize.SMALL,
        )
        result = ProvisioningService(bp).build()
        self.assertIn("pos", result.summary["enabled_modules"])
        self.assertIn("controlled_substance_dispense", result.summary["approval_policies"])
        names = set(Role.objects.filter(tenant_id=bp.tenant_id).values_list("name", flat=True))
        self.assertIn("Pharmacist", names)
        self.assertIn("Pharmacy Technician", names)


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
