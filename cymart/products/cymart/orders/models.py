import uuid

from django.db import models


class MarketplaceOrderStatus(models.TextChoices):
    """CyberCom master spec section 9 — exact state list."""

    DRAFT = "draft", "Draft"
    PENDING_PAYMENT = "pending_payment", "Pending Payment"
    PAYMENT_AUTHORIZED = "payment_authorized", "Payment Authorized"
    SUBMITTED = "submitted", "Submitted"
    MERCHANT_PENDING = "merchant_pending", "Merchant Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    PREPARING = "preparing", "Preparing"
    READY_FOR_PICKUP = "ready_for_pickup", "Ready For Pickup"
    DELIVERY_REQUESTED = "delivery_requested", "Delivery Requested"
    DRIVER_ASSIGNED = "driver_assigned", "Driver Assigned"
    PICKED_UP = "picked_up", "Picked Up"
    IN_TRANSIT = "in_transit", "In Transit"
    DELIVERED = "delivered", "Delivered"
    COMPLETED = "completed", "Completed"
    CANCELLATION_REQUESTED = "cancellation_requested", "Cancellation Requested"
    CANCELLED = "cancelled", "Cancelled"
    REFUND_PENDING = "refund_pending", "Refund Pending"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    REFUNDED = "refunded", "Refunded"
    DISPUTED = "disputed", "Disputed"
    FAILED = "failed", "Failed"


class FulfillmentType(models.TextChoices):
    PICKUP = "pickup", "Pickup"
    MERCHANT_DELIVERY = "merchant_delivery", "Merchant Delivery"
    CYDRIVE_DELIVERY = "cydrive_delivery", "CyDrive Delivery"
    THIRD_PARTY_DELIVERY = "third_party_delivery", "Third-Party Delivery"


# Valid outgoing transitions per state. Anything not listed here as a value
# for the current state is an invalid transition and OrderStateMachine
# raises rather than silently allowing it.
VALID_TRANSITIONS: dict[str, set[str]] = {
    MarketplaceOrderStatus.DRAFT: {
        MarketplaceOrderStatus.PENDING_PAYMENT,
        MarketplaceOrderStatus.CANCELLED,
    },
    MarketplaceOrderStatus.PENDING_PAYMENT: {
        MarketplaceOrderStatus.PAYMENT_AUTHORIZED,
        MarketplaceOrderStatus.FAILED,
        MarketplaceOrderStatus.CANCELLED,
    },
    MarketplaceOrderStatus.PAYMENT_AUTHORIZED: {
        MarketplaceOrderStatus.SUBMITTED,
        MarketplaceOrderStatus.FAILED,
        MarketplaceOrderStatus.CANCELLED,
    },
    MarketplaceOrderStatus.SUBMITTED: {
        MarketplaceOrderStatus.MERCHANT_PENDING,
    },
    MarketplaceOrderStatus.MERCHANT_PENDING: {
        MarketplaceOrderStatus.ACCEPTED,
        MarketplaceOrderStatus.REJECTED,
    },
    MarketplaceOrderStatus.ACCEPTED: {
        MarketplaceOrderStatus.PREPARING,
        MarketplaceOrderStatus.CANCELLATION_REQUESTED,
    },
    MarketplaceOrderStatus.REJECTED: {
        MarketplaceOrderStatus.REFUND_PENDING,
    },
    MarketplaceOrderStatus.PREPARING: {
        MarketplaceOrderStatus.READY_FOR_PICKUP,
        MarketplaceOrderStatus.CANCELLATION_REQUESTED,
    },
    MarketplaceOrderStatus.READY_FOR_PICKUP: {
        MarketplaceOrderStatus.DELIVERY_REQUESTED,
        MarketplaceOrderStatus.DELIVERED,  # direct pickup by customer
    },
    MarketplaceOrderStatus.DELIVERY_REQUESTED: {
        MarketplaceOrderStatus.DRIVER_ASSIGNED,
    },
    MarketplaceOrderStatus.DRIVER_ASSIGNED: {
        MarketplaceOrderStatus.PICKED_UP,
    },
    MarketplaceOrderStatus.PICKED_UP: {
        MarketplaceOrderStatus.IN_TRANSIT,
    },
    MarketplaceOrderStatus.IN_TRANSIT: {
        MarketplaceOrderStatus.DELIVERED,
        MarketplaceOrderStatus.FAILED,
    },
    MarketplaceOrderStatus.DELIVERED: {
        MarketplaceOrderStatus.COMPLETED,
        MarketplaceOrderStatus.DISPUTED,
        MarketplaceOrderStatus.REFUND_PENDING,
    },
    MarketplaceOrderStatus.COMPLETED: {
        MarketplaceOrderStatus.DISPUTED,
        MarketplaceOrderStatus.REFUND_PENDING,
    },
    MarketplaceOrderStatus.CANCELLATION_REQUESTED: {
        MarketplaceOrderStatus.CANCELLED,
        MarketplaceOrderStatus.ACCEPTED,  # merchant declines the cancellation request
    },
    MarketplaceOrderStatus.CANCELLED: {
        MarketplaceOrderStatus.REFUND_PENDING,
    },
    MarketplaceOrderStatus.REFUND_PENDING: {
        MarketplaceOrderStatus.PARTIALLY_REFUNDED,
        MarketplaceOrderStatus.REFUNDED,
    },
    MarketplaceOrderStatus.PARTIALLY_REFUNDED: {
        MarketplaceOrderStatus.REFUNDED,
        MarketplaceOrderStatus.DISPUTED,
    },
    MarketplaceOrderStatus.REFUNDED: set(),
    MarketplaceOrderStatus.DISPUTED: {
        MarketplaceOrderStatus.REFUND_PENDING,
        MarketplaceOrderStatus.COMPLETED,  # dispute resolved in merchant's favor
    },
    MarketplaceOrderStatus.FAILED: set(),
}


class MarketplaceOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Idempotent order creation (master spec requirement + critical test
    # case 12: duplicate webhook delivery must not create duplicate orders).
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)

    tenant_id = models.UUIDField(db_index=True, help_text="The merchant fulfilling this order.")
    store_id = models.UUIDField(db_index=True)
    customer_id = models.UUIDField(db_index=True)
    category_id = models.UUIDField(null=True, blank=True)

    status = models.CharField(
        max_length=32,
        choices=MarketplaceOrderStatus.choices,
        default=MarketplaceOrderStatus.DRAFT,
        db_index=True,
    )
    fulfillment_type = models.CharField(
        max_length=32, choices=FulfillmentType.choices, default=FulfillmentType.PICKUP
    )

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    merchant_funded_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cybercom_funded_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tip_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    customer_notes = models.TextField(blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)

    # Soft reference — set when fulfillment_type == cydrive_delivery, to
    # the CyDrive DeliveryCompany that will fulfill it. Which network-active
    # company gets picked is real routing logic not built yet (Phase 6
    # follow-up); this field just records the decision once made.
    delivery_company_id = models.UUIDField(null=True, blank=True)
    delivery_job_id = models.UUIDField(
        null=True, blank=True, help_text="Set once a CyDrive DeliveryJob is created for this order."
    )

    commission_calculation = models.ForeignKey(
        "cymart_commission.CommissionCalculation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_marketplace_order"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["customer_id", "status"]),
        ]

    def __str__(self):
        return f"MarketplaceOrder({self.id}, {self.status})"


class MarketplaceOrderLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(MarketplaceOrder, on_delete=models.CASCADE, related_name="lines")
    product_id = models.UUIDField()
    product_name_snapshot = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    item_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = "cymart_marketplace_order_line"

    def __str__(self):
        return f"{self.quantity}x {self.product_name_snapshot}"

    @property
    def line_total(self):
        return (self.unit_price * self.quantity) - self.item_discount


class OrderStatusHistory(models.Model):
    """Audit trail of every status transition — separate from platform.audit
    since this is domain-specific (from_status/to_status), not a generic
    audit event. A generic platform.audit entry can still be emitted
    alongside this for cross-product audit search."""

    # Plain auto-incrementing integer PK on purpose, not UUID — this is an
    # append-only sequential log and its ordering has to be genuinely
    # monotonic. created_at alone isn't guaranteed unique at sub-millisecond
    # insert speed (two history rows can tie); a UUID PK would make ties
    # break in effectively random order. Nothing external references this
    # row by ID (see serializer — id isn't even exposed), so there's no
    # reason to force UUID here just for consistency with other models.
    order = models.ForeignKey(
        MarketplaceOrder, on_delete=models.CASCADE, related_name="status_history"
    )
    from_status = models.CharField(max_length=32, blank=True)
    to_status = models.CharField(max_length=32)
    reason = models.CharField(max_length=300, blank=True)
    actor_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_order_status_history"
        ordering = ["id"]

    def __str__(self):
        return f"{self.from_status} -> {self.to_status}"
