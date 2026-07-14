import uuid

from django.db import models


class CommissionScope(models.TextChoices):
    GLOBAL = "global", "Global"
    CATEGORY = "category", "Category"
    MERCHANT = "merchant", "Merchant"
    STORE = "store", "Store"
    PRODUCT = "product", "Product"
    PROMOTIONAL = "promotional", "Promotional"


# More specific scope wins when several policies could apply to the same
# order. Promotional policies (time-boxed campaigns) outrank even a
# product-specific standing policy while they're in their effective window.
SCOPE_SPECIFICITY = {
    CommissionScope.PROMOTIONAL: 5,
    CommissionScope.PRODUCT: 4,
    CommissionScope.STORE: 3,
    CommissionScope.MERCHANT: 2,
    CommissionScope.CATEGORY: 1,
    CommissionScope.GLOBAL: 0,
}


class CommissionBase(models.TextChoices):
    GROSS_MERCHANDISE_VALUE = "gross_merchandise_value", "Gross Merchandise Value"
    GROSS_EXCLUDING_TAX = "gross_excluding_tax", "Gross Value Excluding Tax"
    GROSS_AFTER_MERCHANT_DISCOUNT = (
        "gross_after_merchant_discount",
        "Gross Value After Merchant-Funded Discount",
    )
    GROSS_AFTER_ALL_DISCOUNTS = "gross_after_all_discounts", "Gross Value After All Discounts"
    NET_ITEM_VALUE = "net_item_value", "Net Item Value"


class CommissionPolicy(models.Model):
    """
    A configurable commission rule (CyberCom master spec section 8). Never
    hardcode the commission percentage in application code — the default 5%
    policy is a real, seeded CommissionPolicy row (see
    commission/migrations/0002_seed_global_default_policy.py), not a Python
    constant. CommissionEngine.resolve_policy() only ever reads from this
    table.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    scope = models.CharField(max_length=16, choices=CommissionScope.choices)
    # Soft reference — the category/merchant/store/product this policy
    # applies to. Null for scope=global. No FK: those entities live in
    # CyShop/CyCom/CyMart's own category taxonomy (Phase 3, not yet built),
    # not in this app's database.
    scope_ref_id = models.UUIDField(null=True, blank=True, db_index=True)

    commission_base = models.CharField(
        max_length=32,
        choices=CommissionBase.choices,
        default=CommissionBase.GROSS_AFTER_MERCHANT_DISCOUNT,
    )
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    delivery_excluded = models.BooleanField(default=True)
    tips_excluded = models.BooleanField(default=True)
    taxes_included = models.BooleanField(default=False)

    is_exempt = models.BooleanField(
        default=False, help_text="If true, matching orders pay zero commission."
    )
    requires_approval = models.BooleanField(default=False)
    approved = models.BooleanField(
        default=True, help_text="Ignored unless requires_approval is true."
    )

    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_commission_policy"
        indexes = [
            models.Index(fields=["scope", "scope_ref_id"]),
            models.Index(fields=["effective_from", "effective_until"]),
        ]

    def __str__(self):
        return f"CommissionPolicy({self.scope}, {self.percentage}%)"

    @property
    def is_usable(self) -> bool:
        return self.approved or not self.requires_approval


class CommissionTier(models.Model):
    """
    Tiered commission support: within a single policy, the percentage can
    step up/down by commission-base amount range. If a policy has tiers,
    the engine uses the tier matching the order's commission-base amount
    instead of the policy's own flat `percentage`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(CommissionPolicy, on_delete=models.CASCADE, related_name="tiers")
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = "cymart_commission_tier"
        ordering = ["min_amount"]

    def __str__(self):
        return f"CommissionTier({self.min_amount}-{self.max_amount}, {self.percentage}%)"


class CommissionCalculation(models.Model):
    """
    Immutable ledger entry — one row per commission calculation, including
    reversals (which are their own new row, never a mutation of the
    original). Matches "use immutable ledger entries for financial
    calculations" and "commission engine must generate transparent
    line-level calculation details."
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, help_text="The merchant this commission is on.")

    # Soft reference to the marketplace order this calculation is for.
    # MarketplaceOrder doesn't exist yet (later in Phase 3) — reference by
    # id + type so this ledger is ready before that model lands.
    reference_type = models.CharField(max_length=64, default="marketplace_order")
    reference_id = models.UUIDField(db_index=True)

    policy = models.ForeignKey(
        CommissionPolicy, on_delete=models.PROTECT, related_name="calculations"
    )
    commission_base_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    breakdown = models.JSONField(
        help_text="Transparent line-level detail: base, rate, fixed fee, "
        "min/max clamp applied, exemption, tier used."
    )

    is_refund_reversal = models.BooleanField(default=False)
    reverses = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversal_entries",
        help_text="Set when is_refund_reversal is true — the original calculation being reversed.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_commission_calculation"
        indexes = [
            models.Index(fields=["tenant_id", "reference_id"]),
        ]

    def __str__(self):
        kind = "reversal" if self.is_refund_reversal else "calculation"
        return f"CommissionCalculation({kind}, {self.commission_amount})"
