import uuid
from decimal import Decimal

import pytest

from products.cymart.orders.models import MarketplaceOrderStatus
from products.cymart.orders.services import OrderService
from products.cymart.settlement.services import OrderNotSettleableError, SettlementService


@pytest.mark.django_db
class TestSettlement:
    def _completed_order(self, unit_price=Decimal("100.00")):
        svc = OrderService()
        order, _ = svc.create_order(
            idempotency_key=str(uuid.uuid4()),
            tenant_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            line_items=[{"product_id": uuid.uuid4(), "quantity": "1", "unit_price": str(unit_price)}],
        )
        machine = svc.state_machine
        for status in [
            MarketplaceOrderStatus.PENDING_PAYMENT,
            MarketplaceOrderStatus.PAYMENT_AUTHORIZED,
            MarketplaceOrderStatus.SUBMITTED,
            MarketplaceOrderStatus.MERCHANT_PENDING,
            MarketplaceOrderStatus.ACCEPTED,
            MarketplaceOrderStatus.PREPARING,
            MarketplaceOrderStatus.READY_FOR_PICKUP,
            MarketplaceOrderStatus.DELIVERED,
        ]:
            order = machine.transition(order, status)
        return svc.complete_order(order)

    def test_cannot_settle_before_commission_calculated(self):
        svc = OrderService()
        order, _ = svc.create_order(
            idempotency_key=str(uuid.uuid4()),
            tenant_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            line_items=[{"product_id": uuid.uuid4(), "quantity": "1", "unit_price": "100.00"}],
        )
        with pytest.raises(OrderNotSettleableError):
            SettlementService().generate_for_order(order)

    def test_master_spec_worked_example_matches_settlement(self):
        """Order merchandise value after discount: 100. CyMart commission:
        5%. Merchant gross settlement before other fees: 95."""
        order = self._completed_order()
        entry = SettlementService().generate_for_order(order)
        assert entry.merchant_merchandise_revenue == Decimal("100.00")
        assert entry.cymart_commission == Decimal("5.00")
        assert entry.net_merchant_settlement == Decimal("95.00")
        assert entry.cybercom_net_revenue == Decimal("5.00")

    def test_settlement_ledger_components_sum_correctly(self):
        order = self._completed_order()
        entry = SettlementService().generate_for_order(order)
        # customer_payment should equal merchant net + cymart revenue +
        # taxes + fees not yet integrated (all zero here).
        reconstructed = (
            entry.net_merchant_settlement
            + entry.cybercom_net_revenue
            + entry.net_delivery_company_settlement
        )
        assert reconstructed == entry.customer_payment

    def test_delivery_and_payment_gateway_fields_are_honestly_zero(self):
        order = self._completed_order()
        entry = SettlementService().generate_for_order(order)
        assert entry.delivery_company_amount == Decimal("0")
        assert entry.payment_processing_fee == Decimal("0")
        assert entry.net_delivery_company_settlement == Decimal("0")

    def test_refund_adjustment_reverses_settlement(self):
        order = self._completed_order()
        settlement_svc = SettlementService()
        original = settlement_svc.generate_for_order(order)

        commission_reversal = order.commission_calculation.commission_amount * -1
        adjustment = settlement_svc.generate_refund_adjustment(
            original, commission_reversal_amount=commission_reversal, refund_amount=Decimal("100.00")
        )

        assert adjustment.is_refund_adjustment is True
        assert adjustment.adjusts_id == original.id
        net_after_refund = original.net_merchant_settlement + adjustment.net_merchant_settlement
        assert net_after_refund == Decimal("0.00")
