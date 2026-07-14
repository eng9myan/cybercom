import uuid
from decimal import Decimal

from django.db import transaction

from products.cymart.commission.services import CommissionEngine, OrderContext, OrderLineItem

from .cydrive_client import CyDriveClient, CyDriveIntegrationError
from .models import (
    FulfillmentType,
    MarketplaceOrder,
    MarketplaceOrderLine,
    MarketplaceOrderStatus,
    OrderStatusHistory,
    VALID_TRANSITIONS,
)


class InvalidOrderTransitionError(Exception):
    pass


class OrderStateMachine:
    def transition(
        self,
        order: MarketplaceOrder,
        to_status: str,
        reason: str = "",
        actor_id: uuid.UUID | None = None,
    ) -> MarketplaceOrder:
        allowed = VALID_TRANSITIONS.get(order.status, set())
        if to_status not in allowed:
            raise InvalidOrderTransitionError(
                f"Cannot transition MarketplaceOrder from '{order.status}' to '{to_status}'. "
                f"Allowed: {sorted(allowed) or '(terminal state)'}"
            )
        with transaction.atomic():
            from_status = order.status
            order.status = to_status
            order.save(update_fields=["status", "updated_at"])
            OrderStatusHistory.objects.create(
                order=order,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
                actor_id=actor_id,
            )
        return order


class OrderService:
    def __init__(self):
        self.state_machine = OrderStateMachine()
        self.commission_engine = CommissionEngine()

    def create_order(
        self,
        idempotency_key: str,
        tenant_id: uuid.UUID,
        store_id: uuid.UUID,
        customer_id: uuid.UUID,
        line_items: list[dict],
        category_id: uuid.UUID | None = None,
        fulfillment_type: str = "pickup",
        delivery_fee: Decimal = Decimal("0"),
        tip_amount: Decimal = Decimal("0"),
        tax_amount: Decimal = Decimal("0"),
        cybercom_funded_discount: Decimal = Decimal("0"),
        customer_notes: str = "",
    ) -> tuple[MarketplaceOrder, bool]:
        """
        Idempotent: replaying the same idempotency_key returns the existing
        order instead of creating a duplicate (critical test case 12).
        Returns (order, created).
        """
        existing = MarketplaceOrder.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing, False

        subtotal = sum(
            (Decimal(str(li["unit_price"])) * Decimal(str(li["quantity"])) for li in line_items),
            Decimal("0"),
        )
        merchant_discount = sum(
            (Decimal(str(li.get("item_discount", "0"))) for li in line_items), Decimal("0")
        )
        total = (
            subtotal
            - merchant_discount
            - cybercom_funded_discount
            + tax_amount
            + delivery_fee
            + tip_amount
        )

        with transaction.atomic():
            order = MarketplaceOrder.objects.create(
                idempotency_key=idempotency_key,
                tenant_id=tenant_id,
                store_id=store_id,
                customer_id=customer_id,
                category_id=category_id,
                fulfillment_type=fulfillment_type,
                subtotal=subtotal,
                merchant_funded_discount=merchant_discount,
                cybercom_funded_discount=cybercom_funded_discount,
                tax_amount=tax_amount,
                delivery_fee=delivery_fee,
                tip_amount=tip_amount,
                total_amount=total,
                customer_notes=customer_notes,
            )
            for li in line_items:
                MarketplaceOrderLine.objects.create(
                    order=order,
                    product_id=li["product_id"],
                    product_name_snapshot=li.get("product_name", ""),
                    quantity=Decimal(str(li["quantity"])),
                    unit_price=Decimal(str(li["unit_price"])),
                    item_discount=Decimal(str(li.get("item_discount", "0"))),
                    notes=li.get("notes", ""),
                )
            OrderStatusHistory.objects.create(
                order=order, from_status="", to_status=MarketplaceOrderStatus.DRAFT
            )
        return order, True

    def complete_order(self, order: MarketplaceOrder) -> MarketplaceOrder:
        """Transitions to completed and calculates commission exactly once."""
        order = self.state_machine.transition(order, MarketplaceOrderStatus.COMPLETED)
        if order.commission_calculation_id is None:
            ctx = OrderContext(
                tenant_id=order.tenant_id,
                store_id=order.store_id,
                category_id=order.category_id,
                line_items=[
                    OrderLineItem(
                        product_id=line.product_id,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        item_discount=line.item_discount,
                    )
                    for line in order.lines.all()
                ],
                delivery_fee=order.delivery_fee,
                tip_amount=order.tip_amount,
                tax_amount=order.tax_amount,
                cybercom_funded_discount=order.cybercom_funded_discount,
            )
            calc = self.commission_engine.calculate(ctx, reference_id=order.id)
            order.commission_calculation = calc
            order.save(update_fields=["commission_calculation"])
        return order

    def request_delivery(
        self,
        order: MarketplaceOrder,
        delivery_company_id: uuid.UUID,
        access_token: str,
        pickup_address: dict,
        dropoff_address: dict,
    ) -> MarketplaceOrder:
        """
        Transitions the order to delivery_requested and creates the
        matching CyDrive DeliveryJob in one call. Only valid for
        fulfillment_type == cydrive_delivery — pickup and merchant-delivery
        orders never involve CyDrive at all.

        If CyDrive rejects or is unreachable, the order transition is
        rolled back (transaction.atomic) rather than left in
        delivery_requested with no actual job behind it — that state would
        be a lie about what's really happening.
        """
        if order.fulfillment_type != FulfillmentType.CYDRIVE_DELIVERY:
            raise CyDriveIntegrationError(
                f"Order {order.id} has fulfillment_type '{order.fulfillment_type}', "
                "not cydrive_delivery — nothing to dispatch to CyDrive."
            )

        with transaction.atomic():
            order = self.state_machine.transition(order, MarketplaceOrderStatus.DELIVERY_REQUESTED)
            job = CyDriveClient().create_delivery_job(
                access_token=access_token,
                delivery_company_id=str(delivery_company_id),
                source_order_id=str(order.id),
                pickup_address=pickup_address,
                dropoff_address=dropoff_address,
            )
            order.delivery_company_id = delivery_company_id
            order.delivery_job_id = uuid.UUID(job["id"])
            order.save(update_fields=["delivery_company_id", "delivery_job_id", "updated_at"])
        return order

    def refund_order(self, order: MarketplaceOrder, refund_amount: Decimal) -> MarketplaceOrder:
        """Reverses commission proportionally, then moves the order to the
        correct refund state (partially_refunded vs refunded)."""
        if order.commission_calculation_id is not None:
            self.commission_engine.reverse_for_refund(order.commission_calculation, refund_amount)

        is_full_refund = refund_amount >= order.total_amount
        target = (
            MarketplaceOrderStatus.REFUNDED
            if is_full_refund
            else MarketplaceOrderStatus.PARTIALLY_REFUNDED
        )
        if order.status != MarketplaceOrderStatus.REFUND_PENDING:
            order = self.state_machine.transition(order, MarketplaceOrderStatus.REFUND_PENDING)
        return self.state_machine.transition(order, target)
