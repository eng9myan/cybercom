"""
Whitelist of what a saved report is allowed to query. A report's `source`,
`dimension`, and `measure` are always looked up through this dict — never
used to build a field/attribute name directly from user input — so there's
no way to reach an arbitrary model field (or anything outside it) through
the reporting API.

Only models with a real, DB-stored total qualify as a measure source
(`PurchaseOrder.total_amount` etc. are Python `@property`s computed from
line items, not ORM-aggregatable — deliberately left out rather than faked
with a second query path).
"""

from products.cycom.ar_ap.models import Invoice
from products.cycom.sales.models import SalesOrder

REPORT_SOURCES = {
    "sales_orders": {
        "label": "Sales Orders",
        "model": SalesOrder,
        "dimensions": {
            "status": ("Status", "status"),
            "customer": ("Customer", "customer_name"),
            "salesperson": ("Salesperson", "salesperson"),
        },
        "measures": {
            "count": ("Order Count", None),
            "amount_total": ("Total Amount", "amount_total"),
        },
    },
    "invoices": {
        "label": "Invoices",
        "model": Invoice,
        "dimensions": {
            "status": ("Status", "status"),
            "invoice_type": ("Invoice Type", "invoice_type"),
        },
        "measures": {
            "count": ("Invoice Count", None),
            "amount_total": ("Total Amount", "amount_total"),
            "amount_paid": ("Amount Paid", "amount_paid"),
        },
    },
}


def source_choices():
    return [(key, cfg["label"]) for key, cfg in REPORT_SOURCES.items()]


def dimension_choices(source_key):
    cfg = REPORT_SOURCES.get(source_key, {})
    return [(key, label) for key, (label, _field) in cfg.get("dimensions", {}).items()]


def measure_choices(source_key):
    cfg = REPORT_SOURCES.get(source_key, {})
    return [(key, label) for key, (label, _field) in cfg.get("measures", {}).items()]
