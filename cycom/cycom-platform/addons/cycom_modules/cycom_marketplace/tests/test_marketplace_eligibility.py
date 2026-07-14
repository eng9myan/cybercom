from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCyMartEligibility(TransactionCase):
    """
    CyberCom master spec critical test cases 1 and 3:
      1. "A CyCom manufacturing company without stores cannot appear in CyMart."
      3. "A CyShop merchant without a signed marketplace agreement cannot sell
         on CyMart." (same rule applies to Cycom companies/stores.)
    """

    def _company(self, **vals):
        defaults = {"name": "Test Merchant Co"}
        defaults.update(vals)
        return self.env["res.company"].create(defaults)

    def _pos_config(self, company, **vals):
        # pos.config requires its company to already have payment methods
        # configured (point_of_sale's own _check_company_payment constraint)
        # — use the environment's pre-configured default company rather than
        # a bare freshly-created one, which has none.
        defaults = {"name": "Main Store", "company_id": company.id}
        defaults.update(vals)
        return self.env["pos.config"].create(defaults)

    def test_company_without_store_cannot_be_marketplace_eligible(self):
        company = self._company(operates_customer_facing_store=False)
        with self.assertRaises(ValidationError):
            company.write({"marketplace_eligible": True})

    def test_company_with_store_can_be_marketplace_eligible(self):
        company = self._company(operates_customer_facing_store=True)
        company.write({"marketplace_eligible": True})  # should not raise
        self.assertTrue(company.marketplace_eligible)

    def test_store_cannot_publish_without_signed_agreement(self):
        company = self.env.company
        company.write({"operates_customer_facing_store": True})
        pos = self._pos_config(company)
        with self.assertRaises(ValidationError):
            pos.write({"marketplace_enabled": True})

    def test_store_cannot_publish_when_status_not_active(self):
        company = self.env.company
        company.write({"operates_customer_facing_store": True})
        company.sign_marketplace_agreement()  # status -> application_pending
        pos = self._pos_config(company)
        with self.assertRaises(ValidationError):
            pos.write({"marketplace_enabled": True})

    def test_store_can_publish_once_fully_eligible(self):
        company = self.env.company
        company.write({"operates_customer_facing_store": True})
        company.sign_marketplace_agreement()
        company.write({"marketplace_status": "active"})
        pos = self._pos_config(company)
        pos.write({"marketplace_enabled": True})  # should not raise
        self.assertTrue(pos.marketplace_enabled)

    def test_store_not_marketplace_enabled_can_save_regardless(self):
        company = self.env.company
        company.write({"operates_customer_facing_store": False})
        pos = self._pos_config(company, marketplace_enabled=False)
        self.assertFalse(pos.marketplace_enabled)
