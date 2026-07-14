"""
Commission engine — CyberCom master spec section 8.

Resolution order (most specific wins): promotional > product > store >
merchant > category > global. Exactly one global policy must exist (seeded
by migration 0002) — the engine never falls back to a hardcoded percentage.

Known simplification (documented, not hidden): policy resolution is
order-level using merchant_id/store_id/category_id, not per-line-item. An
order whose lines span multiple categories/products with different
overrides isn't split into per-line commission today — that's real
follow-up work, not silently assumed away.
"""

import uuid
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

from .models import CommissionBase, CommissionCalculation, CommissionPolicy, CommissionScope

TWOPLACES = Decimal("0.01")


class NoApplicableCommissionPolicyError(Exception):
    """Raised when not even a global policy is configured. This should never
    happen in a correctly seeded environment — surfacing it loudly is
    intentional rather than silently defaulting to a hardcoded rate."""


@dataclass
class OrderLineItem:
    product_id: uuid.UUID
    quantity: Decimal
    unit_price: Decimal
    item_discount: Decimal = Decimal("0")  # merchant-funded, per line


@dataclass
class OrderContext:
    tenant_id: uuid.UUID  # merchant
    store_id: uuid.UUID | None
    category_id: uuid.UUID | None
    line_items: list[OrderLineItem] = field(default_factory=list)
    delivery_fee: Decimal = Decimal("0")
    tip_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    cybercom_funded_discount: Decimal = Decimal("0")


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class CommissionEngine:
    def resolve_policy(self, ctx: OrderContext, at: "timezone.datetime | None" = None) -> CommissionPolicy:
        at = at or timezone.now()
        candidates = CommissionPolicy.objects.filter(
            effective_from__lte=at,
        ).filter(
            models_q_effective_until_ok(at)
        )

        best: CommissionPolicy | None = None
        best_specificity = -1
        for policy in candidates:
            if not policy.is_usable:
                continue
            specificity = self._matches(policy, ctx)
            if specificity is None:
                continue
            if specificity > best_specificity:
                best = policy
                best_specificity = specificity

        if best is None:
            raise NoApplicableCommissionPolicyError(
                "No applicable CommissionPolicy found, not even a global "
                "default. Run the seed migration before calculating commission."
            )
        return best

    @staticmethod
    def _matches(policy: CommissionPolicy, ctx: OrderContext) -> int | None:
        from .models import SCOPE_SPECIFICITY

        if policy.scope == CommissionScope.GLOBAL:
            return SCOPE_SPECIFICITY[CommissionScope.GLOBAL]
        if policy.scope == CommissionScope.CATEGORY and policy.scope_ref_id == ctx.category_id:
            return SCOPE_SPECIFICITY[CommissionScope.CATEGORY]
        if policy.scope == CommissionScope.MERCHANT and policy.scope_ref_id == ctx.tenant_id:
            return SCOPE_SPECIFICITY[CommissionScope.MERCHANT]
        if policy.scope == CommissionScope.STORE and policy.scope_ref_id == ctx.store_id:
            return SCOPE_SPECIFICITY[CommissionScope.STORE]
        if policy.scope == CommissionScope.PRODUCT and any(
            li.product_id == policy.scope_ref_id for li in ctx.line_items
        ):
            return SCOPE_SPECIFICITY[CommissionScope.PRODUCT]
        if policy.scope == CommissionScope.PROMOTIONAL and policy.scope_ref_id in (
            ctx.tenant_id,
            ctx.store_id,
            ctx.category_id,
            None,
        ):
            return SCOPE_SPECIFICITY[CommissionScope.PROMOTIONAL]
        return None

    def compute_commission_base_amount(self, ctx: OrderContext, policy: CommissionPolicy) -> Decimal:
        gross = sum((li.unit_price * li.quantity for li in ctx.line_items), Decimal("0"))
        merchant_discount = sum((li.item_discount for li in ctx.line_items), Decimal("0"))

        if policy.commission_base == CommissionBase.GROSS_MERCHANDISE_VALUE:
            amount = gross
        elif policy.commission_base == CommissionBase.GROSS_EXCLUDING_TAX:
            amount = gross
        elif policy.commission_base == CommissionBase.GROSS_AFTER_MERCHANT_DISCOUNT:
            amount = gross - merchant_discount
        elif policy.commission_base == CommissionBase.GROSS_AFTER_ALL_DISCOUNTS:
            amount = gross - merchant_discount - ctx.cybercom_funded_discount
        elif policy.commission_base == CommissionBase.NET_ITEM_VALUE:
            amount = gross - merchant_discount
        else:  # pragma: no cover — exhaustive over CommissionBase.choices
            raise ValueError(f"Unhandled commission_base: {policy.commission_base}")

        if policy.taxes_included:
            amount += ctx.tax_amount

        # Delivery and tips are excluded from the commission base by
        # construction here — OrderContext.delivery_fee/tip_amount are never
        # added to `amount` regardless of policy flags. delivery_excluded /
        # tips_excluded exist on the policy for transparency in the
        # breakdown and for a future per-jurisdiction override, not because
        # this engine currently supports including them.
        return max(amount, Decimal("0"))

    def calculate(self, ctx: OrderContext, reference_id: uuid.UUID) -> CommissionCalculation:
        policy = self.resolve_policy(ctx)
        base_amount = self.compute_commission_base_amount(ctx, policy)

        if policy.is_exempt:
            commission = Decimal("0")
            rate_used = Decimal("0")
            tier_used = None
        else:
            tier = self._matching_tier(policy, base_amount)
            rate_used = tier.percentage if tier else policy.percentage
            tier_used = str(tier.id) if tier else None
            commission = _round(base_amount * rate_used / Decimal("100") + policy.fixed_fee)

            if policy.min_commission is not None:
                commission = max(commission, policy.min_commission)
            if policy.max_commission is not None:
                commission = min(commission, policy.max_commission)

        breakdown = {
            "commission_base": policy.commission_base,
            "commission_base_amount": str(base_amount),
            "rate_percent": str(rate_used),
            "fixed_fee": str(policy.fixed_fee),
            "tier_used": tier_used,
            "min_commission": str(policy.min_commission) if policy.min_commission is not None else None,
            "max_commission": str(policy.max_commission) if policy.max_commission is not None else None,
            "is_exempt": policy.is_exempt,
            "delivery_excluded": policy.delivery_excluded,
            "tips_excluded": policy.tips_excluded,
            "policy_scope": policy.scope,
            "policy_id": str(policy.id),
        }

        return CommissionCalculation.objects.create(
            tenant_id=ctx.tenant_id,
            reference_id=reference_id,
            policy=policy,
            commission_base_amount=base_amount,
            commission_amount=commission,
            breakdown=breakdown,
        )

    @staticmethod
    def _matching_tier(policy: CommissionPolicy, base_amount: Decimal):
        for tier in policy.tiers.all():
            if base_amount < tier.min_amount:
                continue
            if tier.max_amount is not None and base_amount > tier.max_amount:
                continue
            return tier
        return None

    def reverse_for_refund(
        self, original: CommissionCalculation, refund_amount: Decimal
    ) -> CommissionCalculation:
        """
        Reverses commission proportionally to the refunded share of the
        original commission base amount. Full refund => full reversal.
        """
        if original.commission_base_amount == 0:
            proportion = Decimal("0")
        else:
            proportion = min(refund_amount / original.commission_base_amount, Decimal("1"))

        reversal_amount = _round(-(original.commission_amount * proportion))

        breakdown = {
            **original.breakdown,
            "reverses_calculation_id": str(original.id),
            "refund_amount": str(refund_amount),
            "proportion_refunded": str(proportion),
            "original_commission_amount": str(original.commission_amount),
        }

        return CommissionCalculation.objects.create(
            tenant_id=original.tenant_id,
            reference_type=original.reference_type,
            reference_id=original.reference_id,
            policy=original.policy,
            commission_base_amount=-_round(original.commission_base_amount * proportion),
            commission_amount=reversal_amount,
            breakdown=breakdown,
            is_refund_reversal=True,
            reverses=original,
        )


def models_q_effective_until_ok(at):
    from django.db.models import Q

    return Q(effective_until__isnull=True) | Q(effective_until__gte=at)
