"""
Whitelist of what an automation rule is allowed to watch and change.

A rule's `trigger_source`, every condition `field`, and every action target
are resolved through this dict -- never turned into a model/attribute name
straight from user input. That keeps a crafted rule from reaching an
arbitrary model, reading a field it shouldn't, or writing to one that has
real business logic behind it (status transitions with side effects,
computed totals, tenant_id, ...).

`writable` is deliberately much narrower than `fields`: a rule may *read*
an order's total to decide, but may only *write* the handful of columns
that are safe to set without going through a service function.
"""

from products.cycom.ar_ap.models import Invoice
from products.cycom.crm.models import Lead
from products.cycom.helpdesk.models import Ticket
from products.cycom.inventory.models import StockItem
from products.cycom.procurement.models import PurchaseOrder
from products.cycom.project.models import Task
from products.cycom.sales.models import SalesOrder

# field key -> (label, model field path, type)
# type drives both the UI input control and how the condition value is cast.
AUTOMATION_SOURCES = {
    "sales_order": {
        "label": "Sales Order",
        "model": SalesOrder,
        "fields": {
            "status": ("Status", "status", "string"),
            "amount_total": ("Total Amount", "amount_total", "number"),
            "customer_name": ("Customer", "customer_name", "string"),
            "salesperson": ("Salesperson", "salesperson", "string"),
        },
        "writable": {
            "salesperson": ("Salesperson", "salesperson", "string"),
        },
    },
    "purchase_order": {
        "label": "Purchase Order",
        "model": PurchaseOrder,
        # vendor is a FK, not a denormalized name column -- deliberately not
        # exposed as a condition field rather than reaching across the
        # relation from a user-supplied string.
        "fields": {
            "status": ("Status", "status", "string"),
        },
        "writable": {},
    },
    "invoice": {
        "label": "Invoice",
        "model": Invoice,
        "fields": {
            "status": ("Status", "status", "string"),
            "invoice_type": ("Invoice Type", "invoice_type", "string"),
            "amount_total": ("Total Amount", "amount_total", "number"),
            "amount_paid": ("Amount Paid", "amount_paid", "number"),
        },
        "writable": {},
    },
    "lead": {
        "label": "CRM Lead",
        "model": Lead,
        "fields": {
            "stage": ("Stage", "stage", "string"),
            "name": ("Name", "name", "string"),
            "estimated_value": ("Estimated Value", "estimated_value", "number"),
            "probability": ("Probability", "probability", "number"),
            "source": ("Source", "source", "string"),
            "assigned_to": ("Assigned To", "assigned_to", "string"),
        },
        "writable": {
            "stage": ("Stage", "stage", "string"),
            "assigned_to": ("Assigned To", "assigned_to", "string"),
        },
    },
    "ticket": {
        "label": "Helpdesk Ticket",
        "model": Ticket,
        "fields": {
            "priority": ("Priority", "priority", "string"),
            "stage": ("Stage", "stage", "string"),
            "subject": ("Subject", "subject", "string"),
            "team": ("Team", "team", "string"),
            "assignee": ("Assignee", "assignee", "string"),
        },
        "writable": {
            "priority": ("Priority", "priority", "string"),
            "assignee": ("Assignee", "assignee", "string"),
            "team": ("Team", "team", "string"),
        },
    },
    "task": {
        "label": "Project Task",
        "model": Task,
        "fields": {
            "stage": ("Stage", "stage", "string"),
            "priority": ("Priority", "priority", "string"),
            "assignee": ("Assignee", "assignee", "string"),
        },
        "writable": {
            "stage": ("Stage", "stage", "string"),
            "priority": ("Priority", "priority", "string"),
            "assignee": ("Assignee", "assignee", "string"),
        },
    },
    "stock_item": {
        "label": "Stock Item",
        "model": StockItem,
        "fields": {
            "quantity_on_hand": ("Quantity On Hand", "quantity_on_hand", "number"),
        },
        "writable": {},
    },
}

# Conditions. `numeric_only` ones are rejected against a string field so a
# rule can't silently compare "draft" > 100 and never fire.
OPERATORS = {
    "eq": ("is", False),
    "ne": ("is not", False),
    "gt": ("greater than", True),
    "gte": ("greater than or equal", True),
    "lt": ("less than", True),
    "lte": ("less than or equal", True),
    "contains": ("contains", False),
    "changed_to": ("changed to", False),
}

ACTION_TYPES = {
    "set_field": "Set a field",
    "create_task": "Create a project task",
    "create_todo": "Create a to-do (linked to the record)",
    "send_email": "Send an email",
}

TRIGGER_EVENTS = {
    "created": "When a record is created",
    "updated": "When a record is updated",
    "created_or_updated": "When a record is created or updated",
}


def source_config(source_key):
    return AUTOMATION_SOURCES.get(source_key)


def resolve_field(source_key, field_key, writable=False):
    """(label, model_field_path, type) or None -- the only way a rule's
    field string ever becomes a real attribute name."""
    cfg = AUTOMATION_SOURCES.get(source_key)
    if not cfg:
        return None
    return cfg["writable" if writable else "fields"].get(field_key)


def catalog():
    """Everything the rule builder UI needs, in one payload."""
    return {
        "sources": [
            {
                "key": key,
                "label": cfg["label"],
                "fields": [
                    {"key": fk, "label": lbl, "type": ftype}
                    for fk, (lbl, _path, ftype) in cfg["fields"].items()
                ],
                "writable_fields": [
                    {"key": fk, "label": lbl, "type": ftype}
                    for fk, (lbl, _path, ftype) in cfg["writable"].items()
                ],
            }
            for key, cfg in AUTOMATION_SOURCES.items()
        ],
        "operators": [
            {"key": k, "label": lbl, "numeric_only": num} for k, (lbl, num) in OPERATORS.items()
        ],
        "action_types": [{"key": k, "label": v} for k, v in ACTION_TYPES.items()],
        "trigger_events": [{"key": k, "label": v} for k, v in TRIGGER_EVENTS.items()],
    }
