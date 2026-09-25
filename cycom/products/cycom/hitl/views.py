"""
Human-in-the-loop approval inbox — the `app/approvals/page.tsx` frontend
existed with a complete queue/approve/reject UI wired to `/api/hitl/*`, but
no backend implementation existed anywhere (confirmed via repo-wide grep
during a whole-product hardening pass). This app is that backend.

Deliberately sources purchase orders only for now, not the frontend's
other advertised type ("journal_entry"). Journal entries have no
pending-approval concept anywhere in the accounting posting flow today —
`accounting.services.post_journal_entry` is called directly, ungated, by
~10 other apps (sales, POS, payroll, inventory, expenses, manufacturing,
ar_ap, ...). Adding a mandatory approval gate there is a real behavioral
change to a shared, heavily-depended-on code path, not additive plumbing
like this queue is — it needs its own scoping decision (what threshold,
which document_type policy extension, whether ALL apps' postings should
gate on it or only some), not a silent decision bundled into "build the
missing HITL backend." Purchase orders already have real approval
infrastructure (products.cycom.access.approvals + provisioning's
ApprovalPolicy/ApprovalTier) that this queue just surfaces; journal
entries don't, so the queue naturally (and honestly) returns none for
that type rather than fabricating a workflow that doesn't exist yet.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from products.cycom.access.approvals import (
    is_admin,
    require_approval_authority,
    required_approver_role,
    user_holds_role,
)
from products.cycom.procurement.models import PurchaseOrder
from products.cycom.procurement.services import approve_purchase_order, reject_purchase_order


def _user_can_approve(request, tenant_id, document_type, amount):
    """Same authority rule require_approval_authority() enforces, but as a
    boolean check for filtering a list rather than raising -- used to build
    "items awaiting *this* caller's action", not just "items awaiting
    someone's action"."""
    if is_admin(request):
        return True
    role_name = required_approver_role(tenant_id, document_type, amount)
    if role_name is None:
        return False
    return user_holds_role(request, tenant_id, role_name)


def _purchase_order_queue(request):
    tenant_id = request.tenant_id
    items = []
    orders = PurchaseOrder.objects.filter(tenant_id=tenant_id, status="draft").select_related("vendor")
    for order in orders:
        amount = order.total_amount
        if not _user_can_approve(request, tenant_id, "purchase_order", amount):
            continue
        items.append(
            {
                "id": str(order.id),
                "type": "purchase_order",
                "title": f"PO-{str(order.id)[:8]} — {order.vendor.name}",
                "description": f"{amount} {order.currency} awaiting approval",
                "tenant_id": str(tenant_id) if tenant_id else "",
                "company_id": str(order.company_id) if order.company_id else "",
                "payload": {"amount": str(amount), "currency": order.currency, "vendor": order.vendor.name},
            }
        )
    return items


@api_view(["GET"])
@permission_classes([IsAuthenticatedViaClaims])
def hitl_queue(request):
    return Response(_purchase_order_queue(request))


def _get_draft_order_or_404(item_id, tenant_id):
    try:
        return PurchaseOrder.objects.get(id=item_id, tenant_id=tenant_id)
    except (PurchaseOrder.DoesNotExist, ValueError, TypeError):
        raise ValidationError("Item not found.")


@api_view(["POST"])
@permission_classes([IsAuthenticatedViaClaims])
def hitl_approve(request, item_id):
    order = _get_draft_order_or_404(item_id, request.tenant_id)
    if order.status != "draft":
        raise ValidationError(f"PO is '{order.status}', cannot approve.")
    require_approval_authority(request, order.tenant_id, "purchase_order", order.total_amount)
    approve_purchase_order(order)
    return Response({"status": "approved"})


@api_view(["POST"])
@permission_classes([IsAuthenticatedViaClaims])
def hitl_reject(request, item_id):
    order = _get_draft_order_or_404(item_id, request.tenant_id)
    if order.status != "draft":
        raise ValidationError(f"PO is '{order.status}', cannot reject.")
    require_approval_authority(request, order.tenant_id, "purchase_order", order.total_amount)
    reject_purchase_order(order)
    return Response({"status": "rejected"})
