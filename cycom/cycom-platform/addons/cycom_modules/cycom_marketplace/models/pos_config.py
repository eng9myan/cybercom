from odoo import fields, models, api
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    """A pos.config is Cycom's customer-facing "store" entity — the
    equivalent of CyShop's Branch for marketplace publication purposes."""

    _inherit = "pos.config"

    # CyMart publication (per-store — a company may publish only some stores).
    marketplace_enabled = fields.Boolean(default=False)
    # Soft references: CyMart's category taxonomy and commission/settlement/
    # delivery policy models don't exist yet (Phase 3). Real relations land then.
    marketplace_category_ids = fields.Json()
    commission_policy_id = fields.Char()
    settlement_policy_id = fields.Char()
    delivery_policy_id = fields.Char()

    @api.constrains("marketplace_enabled")
    def _check_marketplace_publication_eligibility(self):
        for pos in self:
            if not pos.marketplace_enabled:
                continue
            company = pos.company_id
            if not company.marketplace_agreement_signed:
                raise ValidationError(
                    "Store cannot be published to CyMart: company has not "
                    "signed the marketplace agreement."
                )
            if company.marketplace_status != "active":
                raise ValidationError(
                    "Store cannot be published to CyMart: company "
                    f"marketplace_status is '{company.marketplace_status}', not 'active'."
                )
            if not company.operates_customer_facing_store:
                raise ValidationError(
                    "Store cannot be published to CyMart: company does not "
                    "operate a customer-facing store."
                )
