"""
CyID ecosystem, Phase 8 — cross-network cart/checkout: one wallet debit
pays for line items spanning Cymed (an already-placed pharmacy/lab order,
paid here rather than re-created — see the module docstring in
core/orders/models.py for why a "cart item" never fabricates a new
medical order) and Cyshop (a real retail SalesOrder, placed via Phase 3's
CyID exchange bridge).

Known, accepted limitation: the wallet debit and the local
CheckoutReceipt are wrapped in one atomic transaction, but the cyshop
order is a real cross-process HTTP call — if it succeeds and something
else in this same call then fails, the local rollback can't un-place the
remote cyshop order. Mitigated by doing the cyshop call LAST, after every
local validation and the debit have already succeeded, minimizing that
window. A full saga/compensation flow is real, disproportionate scope
for this phase — flagged here, not silently ignored.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from platform.wallet.models import CheckoutReceipt, CheckoutReceiptLine, CheckoutReceiptLineType
from platform.wallet.services import WalletService
from products.cymed.core.commerce.cyshop_client import CyshopIntegrationError, exchange_and_place_order
from products.cymed.core.orders.models import Order


class CheckoutError(Exception):
    pass


@dataclass
class CymedOrderPaymentItem:
    order_id: str
    amount: Decimal
    description: str = ""


@dataclass
class CyshopCartItem:
    cyshop_tenant_id: str
    company_id: str
    branch_id: str
    item_name: str
    qty: Decimal
    unit_price: Decimal
    description: str = ""

    @property
    def amount(self) -> Decimal:
        return Decimal(self.qty) * Decimal(self.unit_price)


class CrossNetworkCheckoutService:
    @transaction.atomic
    def checkout(
        self,
        person,
        currency: str,
        *,
        cymed_items: "list[CymedOrderPaymentItem] | None" = None,
        cyshop_items: "list[CyshopCartItem] | None" = None,
        cyid_token: str = "",
        customer_name: str = "",
    ) -> CheckoutReceipt:
        cymed_items = cymed_items or []
        cyshop_items = cyshop_items or []
        if not cymed_items and not cyshop_items:
            raise CheckoutError("Cart is empty.")
        if cyshop_items and not cyid_token:
            raise CheckoutError("cyid_token is required to place cyshop items.")

        # Validate every cymed order reference BEFORE moving any money —
        # a bad order_id should never result in a charge. Known, real gap:
        # this doesn't verify the order actually BELONGS to `person` —
        # PersonIdentity has no link to a clinical Patient record yet
        # (deliberately out of scope for this phase; that linkage belongs
        # with the mobile app's medical-record-view work). Anyone with a
        # valid CyID session and a real order UUID could pay it off today.
        # UUIDs aren't practically guessable, but this is not the same as
        # an authorization check and shouldn't be treated as one.
        validated_orders = []
        for item in cymed_items:
            try:
                order = Order.objects.get(id=item.order_id)
            except Order.DoesNotExist as exc:
                raise CheckoutError(f"Cymed order {item.order_id} not found.") from exc
            validated_orders.append((order, item))

        total = sum((item.amount for item in cymed_items), Decimal("0")) + sum(
            (item.amount for item in cyshop_items), Decimal("0")
        )

        debit = WalletService().debit(person, currency, total, reference="cross_network_checkout")
        receipt = CheckoutReceipt.objects.create(
            person=person, wallet_ledger_entry=debit, currency=currency, total_amount=total
        )

        for order, item in validated_orders:
            CheckoutReceiptLine.objects.create(
                receipt=receipt,
                item_type=CheckoutReceiptLineType.CYMED_ORDER,
                external_reference=str(order.id),
                description=item.description or f"Payment for order {order.id}",
                amount=item.amount,
            )

        # Cyshop calls last, per the module docstring's known-limitation note.
        for item in cyshop_items:
            try:
                cyshop_order = exchange_and_place_order(
                    cyid_token,
                    item.cyshop_tenant_id,
                    company_id=item.company_id,
                    branch_id=item.branch_id,
                    customer_name=customer_name or person.display_name,
                    line_items=[
                        {"item_name": item.item_name, "qty": str(item.qty), "unit_price": str(item.unit_price)}
                    ],
                )
            except CyshopIntegrationError as exc:
                raise CheckoutError(f"Cyshop checkout failed: {exc}") from exc
            CheckoutReceiptLine.objects.create(
                receipt=receipt,
                item_type=CheckoutReceiptLineType.CYSHOP_ORDER,
                external_reference=str(cyshop_order.get("id", "")),
                description=item.description or item.item_name,
                amount=item.amount,
            )

        return receipt
