import uuid
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from products.cymart.orders.models import FulfillmentType, MarketplaceOrderStatus
from products.cymart.orders.services import OrderService
from products.cymart.settlement.services import OrderNotSettleableError, SettlementService


@pytest.mark.django_db
class TestSettlement:
    def _ready_order(self, unit_price=Decimal("100.00"), **order_kwargs):
        """Creates an order and drives it up to ready_for_pickup — the
        point where either complete_order() (pickup/merchant-delivery) or
        request_delivery() (cydrive) takes over next."""
        svc = OrderService()
        order, _ = svc.create_order(
            idempotency_key=str(uuid.uuid4()),
            tenant_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            line_items=[{"product_id": uuid.uuid4(), "quantity": "1", "unit_price": str(unit_price)}],
            **order_kwargs,
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
        ]:
            order = machine.transition(order, status)
        return svc, order

    def _completed_order(self, unit_price=Decimal("100.00"), **order_kwargs):
        svc, order = self._ready_order(unit_price=unit_price, **order_kwargs)
        order = svc.state_machine.transition(order, MarketplaceOrderStatus.DELIVERED)
        return svc.complete_order(order)

    @patch("products.cymart.orders.cydrive_client.requests.post")
    def _completed_cydrive_order(self, mock_post, unit_price=Decimal("100.00"), **order_kwargs):
        job_id = uuid.uuid4()
        mock_post.return_value = Mock(ok=True, status_code=201, json=lambda: {"id": str(job_id)})
        svc, order = self._ready_order(
            unit_price=unit_price, fulfillment_type=FulfillmentType.CYDRIVE_DELIVERY, **order_kwargs
        )
        order = svc.request_delivery(
            order,
            delivery_company_id=uuid.uuid4(),
            access_token="tok",
            pickup_address={},
            dropoff_address={},
        )
        order = svc.state_machine.transition(order, MarketplaceOrderStatus.DRIVER_ASSIGNED)
        order = svc.state_machine.transition(order, MarketplaceOrderStatus.PICKED_UP)
        order = svc.state_machine.transition(order, MarketplaceOrderStatus.IN_TRANSIT)
        order = svc.state_machine.transition(order, MarketplaceOrderStatus.DELIVERED)
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
        reconstructed = (
            entry.net_merchant_settlement
            + entry.cybercom_net_revenue
            + entry.net_delivery_company_settlement
        )
        assert reconstructed == entry.customer_payment

    def test_settlement_reconciles_with_nonzero_tax(self):
        """Regression test: taxes used to be silently dropped from the
        net_merchant + cybercom_net + delivery_net == customer_payment
        reconciliation whenever tax_amount was nonzero — masked in every
        earlier test because they all used tax_amount=0 by default."""
        _, order = self._ready_order(tax_amount=Decimal("7.50"))
        order = OrderService().state_machine.transition(order, MarketplaceOrderStatus.DELIVERED)
        order = OrderService().complete_order(order)
        entry = SettlementService().generate_for_order(order)

        assert entry.taxes == Decimal("7.50")
        reconstructed = (
            entry.net_merchant_settlement
            + entry.cybercom_net_revenue
            + entry.net_delivery_company_settlement
        )
        assert reconstructed == entry.customer_payment

    def test_delivery_and_payment_gateway_fields_are_honestly_zero_for_pickup(self):
        order = self._completed_order()
        entry = SettlementService().generate_for_order(order)
        assert entry.delivery_company_amount == Decimal("0")
        assert entry.payment_processing_fee == Decimal("0")
        assert entry.net_delivery_company_settlement == Decimal("0")

    def test_cydrive_fulfilled_order_routes_delivery_fee_and_tip_to_delivery_company(self):
        order = self._completed_cydrive_order(
            delivery_fee=Decimal("6.00"), tip_amount=Decimal("2.00")
        )
        entry = SettlementService().generate_for_order(order)

        assert entry.delivery_company_amount == Decimal("8.00")
        assert entry.net_delivery_company_settlement == Decimal("8.00")
        # Merchant settlement should NOT include the delivery fee/tip now —
        # only merchandise revenue minus commission (plus any tax, which is
        # 0 in this test).
        assert entry.net_merchant_settlement == Decimal("95.00")

        reconstructed = (
            entry.net_merchant_settlement
            + entry.cybercom_net_revenue
            + entry.net_delivery_company_settlement
        )
        assert reconstructed == entry.customer_payment

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
