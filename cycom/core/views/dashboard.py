"""
Real data for the landing "Command Center" dashboard.

Replaces what was previously a page full of hardcoded numbers and a
fabricated named employee in a sample alert (app/dashboard/page.tsx had
literal arrays: GRAPH_DATA, ALERTS mentioning "Khaled Jaber", and a "pulse"
panel claiming "18 online" biometric devices and "Warehouse Locks: Guards
healthy" -- neither biometric devices nor warehouse locks have any real
backend anywhere in cycom). Every number here is a real aggregate query
against real tenant data. An empty tenant sees zeros and empty lists, not
sample data standing in for them.

Deliberately excludes anything with no real backend: there is no biometric
device registry (zk.machine is explicitly unmapped elsewhere in this
codebase) and no "warehouse lock" concept at all, so neither appears here.
"""
from __future__ import annotations

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from products.cycom.automation.models import AutomationRule, AutomationRun
from products.cycom.ar_ap.models import Invoice
from products.cycom.hr.models import Employee, EmployeeDocument
from products.cycom.inventory.models import StockItem
from products.cycom.pos.models import POSSession
from products.cycom.procurement.models import PurchaseOrder
from products.cycom.sales.models import SalesOrder

# Statuses that represent real, recognized revenue for the trend chart --
# a draft quotation isn't revenue yet.
_REVENUE_STATUSES = ["confirmed", "delivered", "invoiced"]
_OPEN_INVOICE_STATUSES = ["draft", "posted", "partial"]
LOW_STOCK_LIMIT = 5
EXPIRY_WINDOW_DAYS = 30
OVERDUE_INVOICE_LIMIT = 5


def _revenue_trend(tenant_id) -> list[dict]:
    today = date.today().replace(day=1)
    months = [today - relativedelta(months=i) for i in range(5, -1, -1)]
    orders = SalesOrder.objects.filter(
        tenant_id=tenant_id, status__in=_REVENUE_STATUSES,
        order_date__gte=months[0], order_date__lt=today + relativedelta(months=1),
    ).values_list("order_date", "amount_total")

    totals = {m.strftime("%Y-%m"): 0.0 for m in months}
    for order_date, amount in orders:
        key = order_date.strftime("%Y-%m")
        if key in totals:
            totals[key] += float(amount or 0)

    return [{"month": m.strftime("%Y-%m"), "revenue": round(totals[m.strftime("%Y-%m")], 2)} for m in months]


def _pending_approvals(tenant_id):
    """Matches hitl.views._purchase_order_queue's own definition of
    "awaiting approval" exactly (status='draft') -- this dashboard and the
    real approvals queue must never disagree about what's pending."""
    return PurchaseOrder.objects.filter(tenant_id=tenant_id, status="draft").select_related("vendor")


def _alerts(tenant_id) -> list[dict]:
    alerts = []

    pending = list(_pending_approvals(tenant_id)[:OVERDUE_INVOICE_LIMIT])
    for po in pending:
        alerts.append({
            "source": "Procurement", "type": "Pending Approval",
            "desc": f"PO to {po.vendor.name} awaiting approval ({po.currency} {po.total_amount:.2f})",
            "urgency": "high", "href": "/purchase", "sort_date": po.created_at.isoformat(),
        })

    expiring = EmployeeDocument.objects.filter(
        tenant_id=tenant_id,
        # No lower bound: an already-lapsed document is MORE urgent than one
        # about to expire, not less, and must not silently drop out of the
        # list just because the date is in the past.
        expiry_date__lte=date.today() + timedelta(days=EXPIRY_WINDOW_DAYS),
    ).select_related("employee").order_by("expiry_date")[:OVERDUE_INVOICE_LIMIT]
    for doc in expiring:
        days_left = (doc.expiry_date - date.today()).days
        when = f"expired {-days_left} day(s) ago" if days_left < 0 else f"expires in {days_left} day(s)"
        alerts.append({
            "source": "HR", "type": "Document Expiring",
            "desc": f"{doc.employee.first_name} {doc.employee.last_name}'s {doc.get_document_type_display()} {when}",
            "urgency": "high" if days_left <= 7 else "medium",
            "href": "/hr/documents", "sort_date": doc.expiry_date.isoformat(),
        })

    overdue = Invoice.objects.filter(
        tenant_id=tenant_id, status__in=_OPEN_INVOICE_STATUSES, due_date__lt=date.today(),
    ).select_related("partner").order_by("due_date")[:OVERDUE_INVOICE_LIMIT]
    for inv in overdue:
        days_over = (date.today() - inv.due_date).days
        outstanding = inv.amount_total - inv.amount_paid
        alerts.append({
            "source": "Finance", "type": "Overdue Invoice",
            "desc": f"{inv.number} ({inv.partner.name}) {days_over}d overdue -- {inv.currency} {outstanding:.2f}",
            "urgency": "high" if days_over > 14 else "medium",
            "href": "/accounting", "sort_date": inv.due_date.isoformat(),
        })

    # min_stock_qty lives on Product, quantity_on_hand on StockItem -- comparing
    # two columns across a join isn't a plain filter() kwarg, so this is
    # filtered in Python. Tenant stock tables are small enough that this
    # isn't a real cost, and it avoids a database-specific F()-across-join
    # expression for one dashboard widget.
    low_stock = [
        item for item in StockItem.objects.filter(tenant_id=tenant_id, product__min_stock_qty__gt=0)
        .select_related("product", "warehouse")
        if item.quantity_on_hand < item.product.min_stock_qty
    ][:OVERDUE_INVOICE_LIMIT]
    for item in low_stock:
        alerts.append({
            "source": "Inventory", "type": "Low Stock",
            "desc": f"{item.product.name} at {item.warehouse.name}: {item.quantity_on_hand} on hand, "
                    f"reorder at {item.product.min_stock_qty}",
            "urgency": "medium", "href": "/inventory", "sort_date": date.today().isoformat(),
        })

    failed_runs = AutomationRun.objects.filter(
        tenant_id=tenant_id, status="failed",
        created_at__gte=timezone.now() - timedelta(days=7),
    ).select_related("rule").order_by("-created_at")[:OVERDUE_INVOICE_LIMIT]
    for run in failed_runs:
        alerts.append({
            "source": "Automation", "type": "Rule Failed",
            "desc": f"'{run.rule.name}' failed: {(run.detail or 'no detail')[:120]}",
            "urgency": "medium", "href": "/automation", "sort_date": run.created_at.isoformat(),
        })

    urgency_rank = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: (urgency_rank.get(a["urgency"], 9), a["sort_date"]), reverse=False)
    for a in alerts:
        a.pop("sort_date", None)
    return alerts[:10]


def _pulse(tenant_id) -> list[dict]:
    headcount = Employee.objects.filter(tenant_id=tenant_id).count()
    open_sessions = POSSession.objects.filter(tenant_id=tenant_id, status="open").count()
    active_rules = AutomationRule.objects.filter(tenant_id=tenant_id, is_active=True).count()
    pending_count = _pending_approvals(tenant_id).count()

    return [
        {"label": "Employees", "value": f"{headcount} active", "tone": "ok"},
        {"label": "POS Sessions", "value": f"{open_sessions} open", "tone": "ok"},
        {"label": "Automation Rules", "value": f"{active_rules} active", "tone": "ok"},
        {"label": "Pending Approvals", "value": str(pending_count), "tone": "warn" if pending_count else "ok"},
    ]


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        tenant_id = request.tenant_id
        return Response({
            "revenue_trend": _revenue_trend(tenant_id),
            "alerts": _alerts(tenant_id),
            "pulse": _pulse(tenant_id),
        })
