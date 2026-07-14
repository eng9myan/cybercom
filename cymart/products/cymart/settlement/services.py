from decimal import Decimal

from products.cymart.orders.models import FulfillmentType

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

        # CyDrive exists now (Phase 5/6) — if this order actually went
        # through it (fulfillment_type + a real delivery_job_id, not just
        # the type flag), delivery_fee and tip route to the delivery
        # company instead of the merchant. Otherwise (pickup, merchant's
        # own delivery, or cydrive_delivery that never got a job created)
        # they stay with the merchant, same as before.
        fulfilled_by_cydrive = (
            order.fulfillment_type == FulfillmentType.CYDRIVE_DELIVERY
            and order.delivery_job_id is not None
        )

        if fulfilled_by_cydrive:
            # Simplification, documented not hidden: CyDrive is assumed to
            # keep 100% of delivery_fee + tip for now. A CyMart-side cut of
            # the delivery fee (the marketplace's delivery commission) is a
            # real, separate business decision not made yet — not invented
            # here.
            delivery_company_amount = order.delivery_fee + order.tip_amount
            net_delivery_company_settlement = delivery_company_amount
            merchant_delivery_share = Decimal("0")
        else:
            delivery_company_amount = Decimal("0")
            net_delivery_company_settlement = Decimal("0")
            merchant_delivery_share = order.delivery_fee + order.tip_amount

        # Tax is a pass-through liability, not merchant or CyberCom revenue
        # — but someone has to be responsible for remitting it, and no
        # separate tax-remittance service exists. Default: the merchant is
        # the collector of record (common pattern), so it's included in
        # their net settlement rather than silently dropped from the
        # reconciliation. Revisit if/when jurisdictions where CyberCom
        # itself remits tax are supported.
        net_merchant_settlement = (
            merchant_merchandise_revenue
            - commission
            - payment_processing_fee
            + merchant_delivery_share
            + order.tax_amount
        )
        cybercom_net_revenue = commission - payment_processing_fee

        breakdown = {
            "order_id": str(order.id),
            "commission_calculation_id": str(order.commission_calculation_id),
            "fulfilled_by_cydrive": fulfilled_by_cydrive,
            "delivery_job_id": str(order.delivery_job_id) if order.delivery_job_id else None,
            "note": "payment_processing_fee is 0 by construction — no real "
            "gateway integrated yet (Phase 7). delivery_company_amount "
            "assumes CyDrive keeps 100% of delivery_fee+tip; a CyMart cut "
            "of the delivery fee isn't decided yet.",
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
            net_delivery_company_settlement=net_delivery_company_settlement,
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
