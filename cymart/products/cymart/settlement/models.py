import uuid

from django.db import models


class SettlementLedgerEntry(models.Model):
    """
    Immutable settlement ledger — master spec section 17's required
    separation of components. One row per order (plus a second, negative
    row for a refund adjustment — never mutates the original, same
    pattern as CommissionCalculation).

    delivery_company_amount and net_delivery_company_settlement are 0 by
    construction here: CyDrive (Phase 5) doesn't exist yet, so there's no
    real delivery company to settle with. payment_processing_fee is 0 for
    the same reason — no real payment gateway integration exists yet
    (Phase 7). Both are real columns, honestly zero, not omitted or faked.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(db_index=True, help_text="The merchant being settled.")

    customer_payment = models.DecimalField(max_digits=12, decimal_places=2)
    merchant_merchandise_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    merchant_funded_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cybercom_funded_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cymart_commission = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_company_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tip = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    net_merchant_settlement = models.DecimalField(max_digits=12, decimal_places=2)
    net_delivery_company_settlement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cybercom_net_revenue = models.DecimalField(max_digits=12, decimal_places=2)

    is_refund_adjustment = models.BooleanField(default=False)
    adjusts = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="adjustment_entries"
    )
    breakdown = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_settlement_ledger_entry"
        indexes = [models.Index(fields=["tenant_id", "order_id"])]

    def __str__(self):
        kind = "adjustment" if self.is_refund_adjustment else "settlement"
        return f"SettlementLedgerEntry({kind}, order={self.order_id}, net={self.net_merchant_settlement})"
