import uuid
from unittest.mock import Mock, patch

import pytest

from products.cymart.orders.cydrive_client import CyDriveIntegrationError
from products.cymart.orders.models import FulfillmentType, MarketplaceOrderStatus
from products.cymart.orders.services import OrderService


@pytest.mark.django_db
class TestCyDriveIntegration:
    """
    Phase 6: CyMart requesting a delivery from CyDrive. cymart and cydrive
    are separate services/databases — this mocks the HTTP boundary rather
    than requiring a live cydrive server, same as the mobile app's API
    client tests mock fetch.
    """

    def _order_ready_for_delivery(self, svc):
        order, _ = svc.create_order(
            idempotency_key=str(uuid.uuid4()),
            tenant_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            line_items=[{"product_id": uuid.uuid4(), "quantity": "1", "unit_price": "50.00"}],
            fulfillment_type=FulfillmentType.CYDRIVE_DELIVERY,
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
        return order

    @patch("products.cymart.orders.cydrive_client.requests.post")
    def test_request_delivery_creates_job_and_transitions_order(self, mock_post):
        job_id = uuid.uuid4()  # CyDrive DeliveryJob.id is a real UUIDField
        mock_post.return_value = Mock(ok=True, status_code=201, json=lambda: {"id": str(job_id)})
        svc = OrderService()
        order = self._order_ready_for_delivery(svc)
        company_id = uuid.uuid4()

        order = svc.request_delivery(
            order,
            delivery_company_id=company_id,
            access_token="tok",
            pickup_address={"line1": "Store"},
            dropoff_address={"line1": "Customer"},
        )

        assert order.status == MarketplaceOrderStatus.DELIVERY_REQUESTED
        assert order.delivery_company_id == company_id
        assert order.delivery_job_id == job_id

        sent_url, sent_kwargs = mock_post.call_args
        assert sent_url[0].endswith("/fleet/jobs/")
        assert sent_kwargs["headers"]["Authorization"] == "Bearer tok"
        assert sent_kwargs["json"]["source_order_id"] == str(order.id)

    @patch("products.cymart.orders.cydrive_client.requests.post")
    def test_cydrive_rejection_rolls_back_order_transition(self, mock_post):
        mock_post.return_value = Mock(ok=False, status_code=409, text="no eligible driver")
        svc = OrderService()
        order = self._order_ready_for_delivery(svc)

        with pytest.raises(CyDriveIntegrationError):
            svc.request_delivery(
                order,
                delivery_company_id=uuid.uuid4(),
                access_token="tok",
                pickup_address={},
                dropoff_address={},
            )

        order.refresh_from_db()
        assert order.status == MarketplaceOrderStatus.READY_FOR_PICKUP  # not stuck in a half-state
        assert order.delivery_job_id is None

    @patch("products.cymart.orders.cydrive_client.requests.post")
    def test_network_failure_rolls_back_order_transition(self, mock_post):
        import requests

        mock_post.side_effect = requests.ConnectionError("connection refused")
        svc = OrderService()
        order = self._order_ready_for_delivery(svc)

        with pytest.raises(CyDriveIntegrationError):
            svc.request_delivery(
                order,
                delivery_company_id=uuid.uuid4(),
                access_token="tok",
                pickup_address={},
                dropoff_address={},
            )

        order.refresh_from_db()
        assert order.status == MarketplaceOrderStatus.READY_FOR_PICKUP

    def test_request_delivery_rejects_non_cydrive_fulfillment(self):
        svc = OrderService()
        order, _ = svc.create_order(
            idempotency_key=str(uuid.uuid4()),
            tenant_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            line_items=[{"product_id": uuid.uuid4(), "quantity": "1", "unit_price": "10.00"}],
            fulfillment_type=FulfillmentType.PICKUP,
        )
        with pytest.raises(CyDriveIntegrationError):
            svc.request_delivery(
                order,
                delivery_company_id=uuid.uuid4(),
                access_token="tok",
                pickup_address={},
                dropoff_address={},
            )
