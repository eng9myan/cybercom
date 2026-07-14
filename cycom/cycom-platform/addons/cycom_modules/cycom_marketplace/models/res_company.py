from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    # CyMart marketplace eligibility (CyberCom master spec section 7).
    # Unlike CyShop, where every company is inherently a customer-facing
    # retail/F&B business, most Cycom companies are NOT customer-facing
    # (factories, construction, consulting, law firms, internal warehouses).
    # This must default False — a company only appears in CyMart if someone
    # explicitly says it operates a customer-facing store.
    operates_customer_facing_store = fields.Boolean(default=False)
    marketplace_eligible = fields.Boolean(default=False)
    marketplace_agreement_signed = fields.Boolean(default=False)
    marketplace_agreement_signed_at = fields.Datetime()
    marketplace_status = fields.Selection(
        [
            ("not_applied", "Not Applied"),
            ("application_pending", "Application Pending"),
            ("documents_required", "Documents Required"),
            ("compliance_review", "Compliance Review"),
            ("approved", "Approved"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("rejected", "Rejected"),
            ("terminated", "Terminated"),
        ],
        default="not_applied",
    )
    merchant_verification_status = fields.Selection(
        [
            ("unverified", "Unverified"),
            ("pending", "Pending"),
            ("verified", "Verified"),
            ("rejected", "Rejected"),
        ],
        default="unverified",
    )

    def sign_marketplace_agreement(self):
        """Records agreement signature. Does not itself grant marketplace_eligible —
        that's a separate compliance-review decision (see marketplace_status)."""
        self.ensure_one()
        vals = {
            "marketplace_agreement_signed": True,
            "marketplace_agreement_signed_at": fields.Datetime.now(),
        }
        if self.marketplace_status == "not_applied":
            vals["marketplace_status"] = "application_pending"
        self.write(vals)

    @api.constrains("operates_customer_facing_store", "marketplace_eligible")
    def _check_marketplace_eligible_requires_store(self):
        for company in self:
            if company.marketplace_eligible and not company.operates_customer_facing_store:
                raise ValidationError(
                    "A company without a customer-facing store cannot be "
                    "marketplace_eligible for CyMart."
                )
