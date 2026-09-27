"""
Whitelist of which real cycom models a tenant may attach custom fields to.

A definition's `model_key` and a values request's `model_key` are resolved
through this dict only -- never turned into an arbitrary app_label/model_name
straight from user input (same posture as automation.registry). Every model
listed here already carries the `attributes` JSONField from
`platform.common.models.AttributesMixin` (canonical-data-model-v1.md §1.1/§3)
-- that field exists for exactly this purpose and was unused anywhere in the
repo before this app, so custom-field values are stored directly on it rather
than in a separate EAV value table.
"""

from products.cycom.ar_ap.models import Partner
from products.cycom.catalog.models import Product
from products.cycom.hr.models import Employee
from products.cycom.procurement.models import PurchaseOrder
from products.cycom.sales.models import SalesOrder

CUSTOMFIELD_MODELS = {
    "product": ("Product", Product),
    "customer_vendor": ("Customer / Vendor", Partner),
    "sales_order": ("Sales Order", SalesOrder),
    "purchase_order": ("Purchase Order", PurchaseOrder),
    "employee": ("Employee", Employee),
}


def resolve_model(model_key):
    """(label, Model) or None -- the only way a model_key ever becomes a real class."""
    return CUSTOMFIELD_MODELS.get(model_key)


def catalog():
    """Everything the "Custom Fields" settings UI needs to populate its model picker."""
    return [{"key": key, "label": label} for key, (label, _model) in CUSTOMFIELD_MODELS.items()]
