"""
Validated, parameterized query plans — each function is hand-written and
reviewed, reading directly from the real ORM. This is the actual mechanism
that lets the Local Memory Agent answer business questions without ever
letting an LLM touch the database or generate its own queries. Adding a new
question type means writing a new function here, not prompting an LLM to
invent one.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from products.cycom.ar_ap.models import Invoice
from products.cycom.hr.models import Employee
from products.cycom.inventory.models import Product, StockItem, Warehouse
from products.cycom.payroll.models import AttendanceRecord
from products.cycom.pos.models import POSOrder


def sales_summary(tenant_id, warehouse_name: str | None = None, period: str = "this_month") -> dict:
    today = date.today()
    if period == "today":
        start = today
    elif period == "this_week":
        start = today - timedelta(days=today.weekday())
    else:  # this_month
        start = today.replace(day=1)

    qs = POSOrder.objects.filter(
        tenant_id=tenant_id, status="paid", created_at__date__gte=start
    )
    warehouse_label = "all branches"
    if warehouse_name:
        qs = qs.filter(session__warehouse__name__icontains=warehouse_name)
        warehouse = Warehouse.objects.filter(
            tenant_id=tenant_id, name__icontains=warehouse_name
        ).first()
        warehouse_label = warehouse.name if warehouse else warehouse_name

    total = qs.aggregate(s=Sum("amount_total"))["s"] or Decimal("0")
    count = qs.count()
    currency = qs.first().currency if qs.exists() else "JOD"

    return {
        "warehouse": warehouse_label,
        "period": period,
        "period_start": start.isoformat(),
        "order_count": count,
        "total_sales": str(total),
        "currency": currency,
    }


def overdue_invoices(tenant_id, invoice_type: str | None = None) -> dict:
    today = date.today()
    qs = Invoice.objects.filter(
        tenant_id=tenant_id, status="posted", due_date__lt=today
    )
    if invoice_type:
        qs = qs.filter(invoice_type=invoice_type)

    overdue = [inv for inv in qs if inv.amount_due > 0]
    total_due = sum((inv.amount_due for inv in overdue), Decimal("0"))

    return {
        "count": len(overdue),
        "total_amount_due": str(total_due),
        "invoice_numbers": [inv.number for inv in overdue[:20]],
    }


def product_stock(tenant_id, product_name: str) -> dict:
    products = Product.objects.filter(tenant_id=tenant_id, name__icontains=product_name)
    if not products.exists():
        return {"found": False, "product_name": product_name}

    results = []
    for product in products:
        items = StockItem.objects.filter(tenant_id=tenant_id, product=product).select_related("warehouse")
        for item in items:
            results.append(
                {
                    "product": product.name,
                    "sku": product.sku,
                    "warehouse": item.warehouse.name,
                    "quantity_on_hand": str(item.quantity_on_hand),
                    "value": str(item.value),
                }
            )
    total_qty = sum((item.quantity_on_hand for item in StockItem.objects.filter(
        tenant_id=tenant_id, product__in=products
    )), Decimal("0"))

    return {"found": True, "total_quantity": str(total_qty), "by_warehouse": results}


def late_employees(tenant_id, on_date: str | None = None) -> dict:
    target_date = date.fromisoformat(on_date) if on_date else date.today()
    records = AttendanceRecord.objects.filter(
        tenant_id=tenant_id, date=target_date, late_minutes__gt=0
    ).select_related("employee")

    return {
        "date": target_date.isoformat(),
        "count": records.count(),
        "employees": [
            {
                "name": f"{r.employee.first_name} {r.employee.last_name}",
                "employee_number": r.employee.employee_number,
                "late_minutes": r.late_minutes,
            }
            for r in records
        ],
    }


PLAN_REGISTRY = {
    "sales_summary": sales_summary,
    "overdue_invoices": overdue_invoices,
    "product_stock": product_stock,
    "late_employees": late_employees,
}
