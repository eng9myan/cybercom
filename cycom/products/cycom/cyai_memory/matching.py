"""
Deterministic question -> (plan_code, params) matching. Keyword/regex based
on purpose — this is the "validated" part of "validated parameterized query
plan": a human-reviewed mapping, not an LLM guessing which query to run.
No paid provider is involved in this step at all.
"""

import re

from products.cycom.inventory.models import Product, Warehouse


def match_question(tenant_id, question: str) -> tuple[str, dict] | None:
    q = question.lower().strip()

    if "overdue" in q and "invoice" in q:
        invoice_type = None
        if "vendor" in q or "bill" in q:
            invoice_type = "vendor"
        elif "customer" in q:
            invoice_type = "customer"
        return "overdue_invoices", {"invoice_type": invoice_type}

    if re.search(r"\blate\b", q) and ("employee" in q or "who" in q or "staff" in q):
        on_date = None
        if "yesterday" in q:
            from datetime import date, timedelta

            on_date = (date.today() - timedelta(days=1)).isoformat()
        return "late_employees", {"on_date": on_date}

    if "stock" in q or "inventory" in q or "how many" in q and "in stock" in q:
        product_name = _extract_product_name(tenant_id, q)
        if product_name:
            return "product_stock", {"product_name": product_name}

    if "sales" in q or "revenue" in q:
        warehouse_name = _extract_warehouse_name(tenant_id, q)
        period = "this_month"
        if "today" in q:
            period = "today"
        elif "this week" in q:
            period = "this_week"
        return "sales_summary", {"warehouse_name": warehouse_name, "period": period}

    return None


def _extract_warehouse_name(tenant_id, q: str) -> str | None:
    for warehouse in Warehouse.objects.filter(tenant_id=tenant_id):
        if warehouse.name.lower() in q:
            return warehouse.name
    return None


def _extract_product_name(tenant_id, q: str) -> str | None:
    for product in Product.objects.filter(tenant_id=tenant_id):
        if product.name.lower() in q:
            return product.name
    # Fallback: "stock of X" / "stock for X" / "current stock of X"
    m = re.search(r"stock (?:of|for|level of)\s+([a-z0-9 \-]+?)(?:\?|$)", q)
    if m:
        return m.group(1).strip()
    return None
