"""
Whitelisted, reportable models + fields. This is the safety boundary for the
Advanced Report Builder: the LLM only ever proposes a JSON query_spec (see
query_engine.py) — it never runs code or touches the ORM directly. Every
spec is validated against this registry before any query executes. Adding a
new reportable model/field means editing this file (reviewed code), not
something the AI can expand on its own.
"""

from products.cycom.accounting.models import JournalLine
from products.cycom.ar_ap.models import Invoice
from products.cycom.inventory.models import StockItem
from products.cycom.pos.models import POSOrder

REPORTABLE_MODELS = {
    "invoice": {
        "model": Invoice,
        "fields": {"id", "number", "invoice_type", "date", "due_date", "status", "amount_subtotal", "amount_tax", "amount_total", "amount_paid"},
        "filter_fields": {"status", "invoice_type", "date", "due_date"},
        "aggregate_fields": {"amount_subtotal", "amount_tax", "amount_total", "amount_paid"},
    },
    "pos_order": {
        "model": POSOrder,
        "fields": {"id", "order_number", "status", "currency", "amount_subtotal", "amount_tax", "amount_total", "created_at"},
        "filter_fields": {"status", "created_at"},
        "aggregate_fields": {"amount_subtotal", "amount_tax", "amount_total"},
    },
    "stock_item": {
        "model": StockItem,
        "fields": {"id", "product__name", "warehouse__name", "quantity_on_hand", "average_cost"},
        "filter_fields": {"product__name", "warehouse__name"},
        "aggregate_fields": {"quantity_on_hand"},
    },
    "journal_line": {
        "model": JournalLine,
        "fields": {"id", "account__name", "account__account_type", "debit", "credit", "description", "entry__date", "entry__status"},
        "filter_fields": {"account__account_type", "entry__date", "entry__status"},
        "aggregate_fields": {"debit", "credit"},
    },
}
