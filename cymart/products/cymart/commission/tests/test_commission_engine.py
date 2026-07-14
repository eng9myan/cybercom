import uuid
from decimal import Decimal

import pytest
from django.utils import timezone

from products.cymart.commission.models import CommissionPolicy, CommissionScope, CommissionTier
from products.cymart.commission.services import (
    CommissionEngine,
    NoApplicableCommissionPolicyError,
    OrderContext,
    OrderLineItem,
)


@pytest.mark.django_db
class TestCommissionEngine:
    """
    CyberCom master spec critical test cases 4, 5, 6:
      4. "A default 5% commission is calculated correctly."
      5. "Merchant-specific commission overrides the default."
      6. "Refunds reverse commission correctly."
    """

    def _ctx(self, **overrides):
        defaults = dict(
            tenant_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            line_items=[
                OrderLineItem(
                    product_id=uuid.uuid4(),
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00"),
                    item_discount=Decimal("0.00"),
                )
            ],
        )
        defaults.update(overrides)
        return OrderContext(**defaults)

    # ── Test case 4 ──────────────────────────────────────────────────────
    def test_default_5_percent_commission_calculated_correctly(self):
        ctx = self._ctx()
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_base_amount == Decimal("100.00")
        assert calc.commission_amount == Decimal("5.00")
        assert calc.breakdown["policy_scope"] == CommissionScope.GLOBAL
        assert calc.breakdown["rate_percent"] == "5.00"

    def test_no_seeded_policy_raises_instead_of_hardcoding(self):
        CommissionPolicy.objects.filter(scope="global").delete()
        ctx = self._ctx()
        with pytest.raises(NoApplicableCommissionPolicyError):
            CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())

    # ── Test case 5 ──────────────────────────────────────────────────────
    def test_merchant_specific_commission_overrides_default(self):
        ctx = self._ctx()
        CommissionPolicy.objects.create(
            scope=CommissionScope.MERCHANT,
            scope_ref_id=ctx.tenant_id,
            percentage=Decimal("8.50"),
            effective_from=timezone.now(),
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("8.50")
        assert calc.breakdown["policy_scope"] == CommissionScope.MERCHANT

    def test_store_specific_outranks_merchant_specific(self):
        ctx = self._ctx()
        CommissionPolicy.objects.create(
            scope=CommissionScope.MERCHANT,
            scope_ref_id=ctx.tenant_id,
            percentage=Decimal("8.50"),
            effective_from=timezone.now(),
        )
        CommissionPolicy.objects.create(
            scope=CommissionScope.STORE,
            scope_ref_id=ctx.store_id,
            percentage=Decimal("3.00"),
            effective_from=timezone.now(),
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("3.00")
        assert calc.breakdown["policy_scope"] == CommissionScope.STORE

    def test_category_override_applies_when_no_more_specific_policy(self):
        ctx = self._ctx()
        CommissionPolicy.objects.create(
            scope=CommissionScope.CATEGORY,
            scope_ref_id=ctx.category_id,
            percentage=Decimal("6.00"),
            effective_from=timezone.now(),
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("6.00")

    def test_expired_override_falls_back_to_global(self):
        ctx = self._ctx()
        now = timezone.now()
        CommissionPolicy.objects.create(
            scope=CommissionScope.MERCHANT,
            scope_ref_id=ctx.tenant_id,
            percentage=Decimal("8.50"),
            effective_from=now - timezone.timedelta(days=30),
            effective_until=now - timezone.timedelta(days=1),
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("5.00")

    def test_unapproved_override_requiring_approval_is_ignored(self):
        ctx = self._ctx()
        CommissionPolicy.objects.create(
            scope=CommissionScope.MERCHANT,
            scope_ref_id=ctx.tenant_id,
            percentage=Decimal("1.00"),
            requires_approval=True,
            approved=False,
            effective_from=timezone.now(),
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("5.00")

    def test_exempt_policy_produces_zero_commission(self):
        ctx = self._ctx()
        CommissionPolicy.objects.create(
            scope=CommissionScope.MERCHANT,
            scope_ref_id=ctx.tenant_id,
            percentage=Decimal("5.00"),
            is_exempt=True,
            effective_from=timezone.now(),
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("0.00")

    def test_min_max_commission_clamp(self):
        ctx = self._ctx(
            line_items=[
                OrderLineItem(
                    product_id=uuid.uuid4(),
                    quantity=Decimal("1"),
                    unit_price=Decimal("10.00"),
                )
            ]
        )
        CommissionPolicy.objects.create(
            scope=CommissionScope.MERCHANT,
            scope_ref_id=ctx.tenant_id,
            percentage=Decimal("5.00"),
            min_commission=Decimal("2.00"),
            effective_from=timezone.now(),
        )
        # 5% of 10.00 = 0.50, clamped up to the 2.00 minimum.
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("2.00")

    def test_tiered_commission_uses_matching_tier(self):
        ctx = self._ctx(
            line_items=[
                OrderLineItem(
                    product_id=uuid.uuid4(),
                    quantity=Decimal("1"),
                    unit_price=Decimal("500.00"),
                )
            ]
        )
        policy = CommissionPolicy.objects.create(
            scope=CommissionScope.MERCHANT,
            scope_ref_id=ctx.tenant_id,
            percentage=Decimal("5.00"),  # should be ignored — tier wins
            effective_from=timezone.now(),
        )
        CommissionTier.objects.create(
            policy=policy, min_amount=Decimal("0"), max_amount=Decimal("99.99"), percentage=Decimal("5.00")
        )
        CommissionTier.objects.create(
            policy=policy, min_amount=Decimal("100"), max_amount=None, percentage=Decimal("3.00")
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("15.00")  # 3% of 500
        assert calc.breakdown["tier_used"] is not None

    def test_merchant_funded_discount_reduces_commission_base(self):
        ctx = self._ctx(
            line_items=[
                OrderLineItem(
                    product_id=uuid.uuid4(),
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00"),
                    item_discount=Decimal("20.00"),
                )
            ]
        )
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_base_amount == Decimal("80.00")
        assert calc.commission_amount == Decimal("4.00")

    def test_delivery_and_tips_never_enter_commission_base(self):
        ctx = self._ctx(delivery_fee=Decimal("15.00"), tip_amount=Decimal("10.00"))
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        # Still just 5% of the 100.00 merchandise value — delivery/tip ignored.
        assert calc.commission_base_amount == Decimal("100.00")
        assert calc.commission_amount == Decimal("5.00")

    # ── Test case 6 ──────────────────────────────────────────────────────
    def test_full_refund_reverses_commission_completely(self):
        ctx = self._ctx()
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        reversal = CommissionEngine().reverse_for_refund(calc, refund_amount=Decimal("100.00"))
        assert reversal.commission_amount == Decimal("-5.00")
        assert reversal.is_refund_reversal is True
        assert reversal.reverses_id == calc.id

    def test_partial_refund_reverses_commission_proportionally(self):
        ctx = self._ctx()
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        # Half the merchandise value refunded -> half the commission reversed.
        reversal = CommissionEngine().reverse_for_refund(calc, refund_amount=Decimal("50.00"))
        assert reversal.commission_amount == Decimal("-2.50")

    def test_net_commission_after_full_refund_is_zero(self):
        ctx = self._ctx()
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        reversal = CommissionEngine().reverse_for_refund(calc, refund_amount=Decimal("100.00"))
        net = calc.commission_amount + reversal.commission_amount
        assert net == Decimal("0.00")

    # ── Master spec worked example (section 8) ──────────────────────────
    def test_master_spec_worked_example(self):
        """Order merchandise value after discount: 100. CyMart commission:
        5%. CyberCom commission: 5. Merchant gross settlement before other
        fees: 95."""
        ctx = self._ctx()
        calc = CommissionEngine().calculate(ctx, reference_id=uuid.uuid4())
        assert calc.commission_amount == Decimal("5.00")
        merchant_gross_settlement = calc.commission_base_amount - calc.commission_amount
        assert merchant_gross_settlement == Decimal("95.00")
