from decimal import Decimal

from .models import SettlementLedgerEntry


class OrderNotSettleableError(Exception):
    pass


class SettlementService:
    def generate_for_order(self, order) -> SettlementLedgerEntry:
        """
        Builds the settlement ledger entry for a completed order. Requires
        commission to already be calculated (complete_order() in the
        orders app does this) — settlement without a commission figure
        would mean guessing cybercom_net_revenue, which this refuses to do.
        """
        if order.commission_calculation_id is None:
            raise OrderNotSettleableError(
                f"Order {order.id} has no commission_calculation yet — "
                "call OrderService.complete_order() first."
            )

        commission = order.commission_calculation.commission_amount
        merchant_merchandise_revenue = (
            order.subtotal - order.merchant_funded_discount - order.cybercom_funded_discount
        )
        payment_processing_fee = Decimal("0")  # Phase 7 — no real gateway integrated yet
        delivery_company_amount = Decimal("0")  # Phase 5/6 — no CyDrive yet

        # With no delivery company involved yet, delivery fee and tip stay
        # with the merchant — once CyDrive exists (Phase 6), this routes to
        # net_delivery_company_settlement instead based on fulfillment_type.
        net_merchant_settlement = (
            merchant_merchandise_revenue
            - commission
            - payment_processing_fee
            + order.delivery_fee
            + order.tip_amount
            - delivery_company_amount
        )
        cybercom_net_revenue = commission - payment_processing_fee

        breakdown = {
            "order_id": str(order.id),
            "commission_calculation_id": str(order.commission_calculation_id),
            "note": "delivery_company_amount and payment_processing_fee are "
            "0 by construction — CyDrive and payment gateway integration "
            "don't exist yet (Phase 5/6/7).",
        }

        return SettlementLedgerEntry.objects.create(
            order_id=order.id,
            tenant_id=order.tenant_id,
            customer_payment=order.total_amount,
            merchant_merchandise_revenue=merchant_merchandise_revenue,
            taxes=order.tax_amount,
            merchant_funded_discount=order.merchant_funded_discount,
            cybercom_funded_discount=order.cybercom_funded_discount,
            cymart_commission=commission,
            delivery_fee=order.delivery_fee,
            delivery_company_amount=delivery_company_amount,
            payment_processing_fee=payment_processing_fee,
            tip=order.tip_amount,
            net_merchant_settlement=net_merchant_settlement,
            net_delivery_company_settlement=Decimal("0"),
            cybercom_net_revenue=cybercom_net_revenue,
            breakdown=breakdown,
        )

    def generate_refund_adjustment(
        self, original: SettlementLedgerEntry, commission_reversal_amount: Decimal, refund_amount: Decimal
    ) -> SettlementLedgerEntry:
        """commission_reversal_amount is negative (from CommissionEngine.
        reverse_for_refund) — this adjustment entry mirrors that sign."""
        proportion = (
            Decimal("0")
            if original.merchant_merchandise_revenue == 0
            else min(refund_amount / original.merchant_merchandise_revenue, Decimal("1"))
        )
        revenue_reversed = -(original.merchant_merchandise_revenue * proportion)
        net_merchant_reversed = revenue_reversed - commission_reversal_amount

        return SettlementLedgerEntry.objects.create(
            order_id=original.order_id,
            tenant_id=original.tenant_id,
            customer_payment=-(original.customer_payment * proportion),
            merchant_merchandise_revenue=revenue_reversed,
            taxes=Decimal("0"),
            merchant_funded_discount=Decimal("0"),
            cybercom_funded_discount=Decimal("0"),
            cymart_commission=commission_reversal_amount,
            delivery_fee=Decimal("0"),
            delivery_company_amount=Decimal("0"),
            payment_processing_fee=Decimal("0"),
            tip=Decimal("0"),
            net_merchant_settlement=net_merchant_reversed,
            net_delivery_company_settlement=Decimal("0"),
            cybercom_net_revenue=commission_reversal_amount,
            is_refund_adjustment=True,
            adjusts=original,
            breakdown={"refund_amount": str(refund_amount), "proportion": str(proportion)},
        )
