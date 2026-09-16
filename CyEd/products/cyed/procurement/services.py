"""
Procurement services: the approval chain, and the receive-goods step that links
Procurement → Inventory (stock moves) and Procurement → Accounting (GL posting).
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone


class ProcurementError(Exception):
    """Raised for workflow violations (wrong state, over-receipt, …)."""


class SelfApprovalError(ProcurementError):
    """Raised when someone tries to approve a request they raised themselves."""


# ── Approval chain ───────────────────────────────────────────────────────────
def submit_request(request_obj, actor=""):
    """Move a draft request into the approval chain, creating its steps."""
    from products.cyed.procurement.models import ApprovalStep

    if request_obj.status != "draft":
        raise ProcurementError(f"Only a draft request can be submitted (is '{request_obj.status}').")
    if not request_obj.lines.exists():
        raise ProcurementError("Add at least one line before submitting.")

    request_obj.approvals.all().delete()
    ApprovalStep.objects.create(tenant_id=request_obj.tenant_id, request=request_obj, level=1)
    if request_obj.needs_second_approval:
        ApprovalStep.objects.create(tenant_id=request_obj.tenant_id, request=request_obj, level=2)

    request_obj.status = "submitted"
    request_obj.requested_by = request_obj.requested_by or actor
    request_obj.save()
    return request_obj


def decide_request(request_obj, *, level, decision, approver="", comment=""):
    """
    Record one approval decision. Level 1 must be decided before level 2. A
    rejection at any level rejects the whole request.

    Segregation of duties: the person who raised a request may never approve it,
    even if they hold the finance or leadership role.
    """
    if request_obj.status not in ("submitted", "approved_l1"):
        raise ProcurementError(f"Request is '{request_obj.status}' and cannot be decided.")

    requester = (request_obj.requested_by or "").strip().lower()
    if decision == "approved" and requester and requester == (approver or "").strip().lower():
        raise SelfApprovalError("You cannot approve a purchase request you raised yourself.")

    step = request_obj.approvals.filter(level=level).first()
    if step is None:
        raise ProcurementError(f"This request has no level-{level} approval step.")
    if step.decision != "pending":
        raise ProcurementError(f"Level {level} was already {step.decision}.")
    if level == 2:
        first = request_obj.approvals.filter(level=1).first()
        if first and first.decision != "approved":
            raise ProcurementError("Level 1 must approve before level 2.")

    step.decision = decision
    step.approver = approver
    step.comment = comment[:500]
    step.decided_at = timezone.now()
    step.save()

    if decision == "rejected":
        request_obj.status = "rejected"
    elif request_obj.approvals.filter(decision="pending").exists():
        request_obj.status = "approved_l1"
    else:
        request_obj.status = "approved"
    request_obj.save()
    return request_obj


@transaction.atomic
def convert_to_order(request_obj, *, supplier=None, reference=""):
    """Turn a fully approved request into a purchase order, carrying the lines."""
    from products.cyed.procurement.models import PurchaseOrder, PurchaseOrderLine

    if request_obj.status != "approved":
        raise ProcurementError("Only a fully approved request can become a purchase order.")
    if request_obj.purchase_order_id:
        raise ProcurementError("This request has already been converted.")

    supplier = supplier or request_obj.suggested_supplier
    if supplier is None:
        raise ProcurementError("A supplier is required to raise a purchase order.")

    po = PurchaseOrder.objects.create(
        tenant_id=request_obj.tenant_id, supplier=supplier,
        reference=reference or f"PO-{str(request_obj.id)[:8]}",
        status="ordered", order_date=timezone.localdate(),
    )
    for line in request_obj.lines.all():
        PurchaseOrderLine.objects.create(
            tenant_id=request_obj.tenant_id, purchase_order=po, description=line.description,
            quantity=line.quantity, unit_price=line.estimated_unit_price,
            inventory_item=line.inventory_item,
        )
    request_obj.purchase_order = po
    request_obj.status = "converted"
    request_obj.save()
    return po


# ── Goods receipt → Inventory + Accounting ───────────────────────────────────
def _account(tenant_id, code, name, account_type):
    """Fetch or create a GL account, so posting never fails on a missing code."""
    from products.cyed.finance.models import Account

    acc, _ = Account.objects.get_or_create(
        tenant_id=tenant_id, code=code, defaults={"name": name, "account_type": account_type},
    )
    return acc


@transaction.atomic
def receive_goods(purchase_order, *, lines, received_by="", delivery_note="", post_to_gl=True):
    """
    Receive `lines` = [{purchase_order_line_id, quantity}] against a PO.

    For each line: increments InventoryItem.on_hand via a StockMove, and records
    quantity_received on the PO line. Over-receipt is rejected. Once all lines
    are fully received the PO becomes 'received', otherwise 'partially_received'.
    Posts Dr Inventory / Cr Accounts Payable for the received value.
    """
    from products.cyed.finance.services import post_entry
    from products.cyed.inventory.models import StockMove
    from products.cyed.procurement.models import GoodsReceipt, GoodsReceiptLine, PurchaseOrderLine

    if purchase_order.status in ("cancelled", "draft"):
        raise ProcurementError(f"Cannot receive against a '{purchase_order.status}' order.")
    if not lines:
        raise ProcurementError("Nothing to receive.")

    receipt = GoodsReceipt.objects.create(
        tenant_id=purchase_order.tenant_id, purchase_order=purchase_order,
        received_date=timezone.localdate(), received_by=received_by, delivery_note=delivery_note,
    )

    total_value = Decimal("0")
    for entry in lines:
        po_line = PurchaseOrderLine.objects.filter(
            tenant_id=purchase_order.tenant_id, purchase_order=purchase_order,
            id=entry["purchase_order_line_id"],
        ).first()
        if po_line is None:
            raise ProcurementError(f"Line {entry['purchase_order_line_id']} is not on this order.")

        qty = Decimal(str(entry.get("quantity", 0)))
        if qty <= 0:
            raise ProcurementError("Received quantity must be greater than zero.")
        if qty > po_line.quantity_outstanding:
            raise ProcurementError(
                f"Cannot receive {qty} of '{po_line.description}': only "
                f"{po_line.quantity_outstanding} outstanding."
            )

        move = None
        if po_line.inventory_item_id:
            move = StockMove.objects.create(
                tenant_id=purchase_order.tenant_id, item=po_line.inventory_item, move_type="in",
                quantity=qty, reason="Goods received",
                reference=delivery_note or str(purchase_order.reference or purchase_order.id),
            )
            item = po_line.inventory_item
            item.on_hand = Decimal(item.on_hand) + qty
            item.save(update_fields=["on_hand", "updated_at"])

        GoodsReceiptLine.objects.create(
            tenant_id=purchase_order.tenant_id, receipt=receipt, purchase_order_line=po_line,
            quantity_received=qty, stock_move=move,
        )
        po_line.quantity_received = Decimal(po_line.quantity_received) + qty
        po_line.save(update_fields=["quantity_received", "updated_at"])
        total_value += qty * Decimal(po_line.unit_price)

    # Roll the PO status forward from its lines. Query the table directly rather
    # than `purchase_order.lines.all()`, which may return a prefetch cache
    # populated before this receipt updated quantity_received.
    all_lines = PurchaseOrderLine.objects.filter(
        tenant_id=purchase_order.tenant_id, purchase_order=purchase_order
    )
    if all_lines.exists() and all(l.quantity_outstanding <= 0 for l in all_lines):
        purchase_order.status = "received"
    else:
        purchase_order.status = "partially_received"
    purchase_order.save(update_fields=["status", "updated_at"])

    if post_to_gl and total_value > 0:
        inventory_acc = _account(purchase_order.tenant_id, "1400", "Inventory", "asset")
        payable_acc = _account(purchase_order.tenant_id, "2100", "Accounts Payable", "liability")
        receipt.journal_entry = post_entry(
            tenant_id=purchase_order.tenant_id, date=timezone.localdate(),
            reference=f"GRN-{str(receipt.id)[:8]}",
            narration=f"Goods received from {purchase_order.supplier.name}",
            lines=[
                {"account_id": inventory_acc.id, "debit": total_value, "credit": 0,
                 "description": "Stock received"},
                {"account_id": payable_acc.id, "debit": 0, "credit": total_value,
                 "description": f"Payable to {purchase_order.supplier.name}"},
            ],
        )
        receipt.save(update_fields=["journal_entry", "updated_at"])

    return receipt
