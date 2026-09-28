"""
Turns a human-reviewed ParsedDocument into a real *draft* record.

Deliberately thin: every business rule (line validation, gapless number
allocation, header totals) lives in the real InvoiceSerializer /
PurchaseOrderSerializer, which this module calls server-side rather than
duplicating. What it adds is only what those serializers can't know:

- mapping the AI schema (`invoice_date`, `line_items[].amount`, ...) onto
  the real models' fields;
- the FKs the AI can't read off a page (partner, accounts, warehouse,
  per-line products), which the reviewer picks explicitly;
- a tenant-ownership check on every one of those FKs. The real serializers
  use DRF's default unscoped PrimaryKeyRelatedField querysets, so without
  this a crafted id could attach another tenant's account/partner.

The created record is a draft: an invoice still has to be posted and a PO
still has to be approved through their normal flows.
"""
from __future__ import annotations

import datetime
import uuid
from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.ar_ap.serializers import InvoiceSerializer
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.serializers import PurchaseOrderSerializer

APPLICABLE_TYPES = ("invoice", "purchase_order")
INVOICE_TYPES = ("vendor", "customer")


class ApplyError(Exception):
    """Carries a DRF-style error dict back to the view as a 400."""

    def __init__(self, errors):
        super().__init__(str(errors))
        self.errors = errors


def _owned(model, pk, tenant_id, field):
    if not pk:
        raise ApplyError({field: "This field is required."})
    try:
        uuid.UUID(str(pk))
    except ValueError:
        raise ApplyError({field: "Not a valid id."})
    obj = model.objects.filter(pk=pk, tenant_id=tenant_id).first()
    if obj is None:
        raise ApplyError({field: "Not found."})
    if model is Account and not obj.is_postable:
        # Fail now, not later at post time with a draft nobody can post.
        raise ApplyError({field: f"'{obj.code}' is a group/header account; pick a postable account."})
    return obj


def _decimal(value, *, field):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        raise ApplyError({field: f"'{value}' is not a number."})


def _date(value, *, field):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        return datetime.date.fromisoformat(str(value).strip())
    except ValueError:
        raise ApplyError({field: f"'{value}' is not a YYYY-MM-DD date."})


def _currency(reviewed):
    code = (reviewed.get("currency") or "").strip().upper()
    return code or None


def _lines(reviewed, *, price_places):
    """Normalises reviewed line_items to (description, quantity, unit_price).
    A missing quantity means 1 (a services/amount-only line); a missing unit
    price is derived from amount / quantity. Neither -> an error naming the
    line, never a silent zero."""
    items = reviewed.get("line_items") or []
    if not isinstance(items, list) or not items:
        raise ApplyError({"line_items": "At least one line item is required."})
    out = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ApplyError({"line_items": f"Line {idx + 1} is malformed."})
        field = f"line_items[{idx}]"
        qty = _decimal(item.get("quantity"), field=f"{field}.quantity") or Decimal("1")
        if qty <= 0:
            raise ApplyError({f"{field}.quantity": "Quantity must be greater than zero."})
        price = _decimal(item.get("unit_price"), field=f"{field}.unit_price")
        if price is None:
            amount = _decimal(item.get("amount"), field=f"{field}.amount")
            if amount is None:
                raise ApplyError({field: "Line needs a unit price or an amount."})
            price = amount / qty
        price = price.quantize(Decimal(1).scaleb(-price_places))
        description = str(item.get("description") or "").strip()[:255]
        out.append((description, qty, price))
    return out


def _run(serializer_class, payload, request):
    ser = serializer_class(data=payload, context={"request": request})
    if not ser.is_valid():
        raise ApplyError(ser.errors)
    return ser.save(tenant_id=request.tenant_id)


def apply_invoice(doc, params, request):
    tenant_id = request.tenant_id
    reviewed = doc.reviewed_data or {}

    invoice_type = params.get("invoice_type") or "vendor"
    if invoice_type not in INVOICE_TYPES:
        raise ApplyError({"invoice_type": f"Must be one of {', '.join(INVOICE_TYPES)}."})
    partner = _owned(Partner, params.get("partner"), tenant_id, "partner")
    control = _owned(Account, params.get("control_account"), tenant_id, "control_account")
    line_account = _owned(Account, params.get("line_account"), tenant_id, "line_account")

    tax_percent = _decimal(params.get("tax_percent"), field="tax_percent") or Decimal("0")
    if tax_percent < 0 or tax_percent > 100:
        raise ApplyError({"tax_percent": "Must be between 0 and 100."})
    tax_account = None
    if params.get("tax_account"):
        tax_account = _owned(Account, params.get("tax_account"), tenant_id, "tax_account")
    if tax_percent > 0 and tax_account is None:
        raise ApplyError({"tax_account": "Required when a tax percent is set."})

    date = _date(reviewed.get("invoice_date"), field="invoice_date") or datetime.date.today()
    due_date = _date(reviewed.get("due_date"), field="due_date") or (
        date + datetime.timedelta(days=partner.payment_terms_days or 0)
    )
    if due_date < date:
        raise ApplyError({"due_date": "Due date cannot be before the invoice date."})

    payload = {
        "invoice_type": invoice_type,
        "partner": str(partner.pk),
        "date": date.isoformat(),
        "due_date": due_date.isoformat(),
        "control_account": str(control.pk),
        "tax_account": str(tax_account.pk) if tax_account else None,
        "lines": [
            {
                "account": str(line_account.pk),
                "description": description,
                "quantity": str(qty),
                "unit_price": str(price),
                "tax_percent": str(tax_percent),
            }
            for description, qty, price in _lines(reviewed, price_places=2)
        ],
    }
    currency = _currency(reviewed)
    if currency:
        payload["currency"] = currency
    return _run(InvoiceSerializer, payload, request)


def apply_purchase_order(doc, params, request):
    tenant_id = request.tenant_id
    reviewed = doc.reviewed_data or {}

    vendor = _owned(Partner, params.get("vendor"), tenant_id, "vendor")
    warehouse = _owned(Warehouse, params.get("warehouse"), tenant_id, "warehouse")
    offset = _owned(Account, params.get("offset_account"), tenant_id, "offset_account")

    lines = _lines(reviewed, price_places=4)
    product_ids = params.get("line_products")
    if not isinstance(product_ids, list) or len(product_ids) != len(lines):
        raise ApplyError({"line_products": f"Pick a product for each of the {len(lines)} line(s)."})
    products = [
        _owned(Product, pid, tenant_id, f"line_products[{idx}]")
        for idx, pid in enumerate(product_ids)
    ]

    payload = {
        "vendor": str(vendor.pk),
        "warehouse": str(warehouse.pk),
        "lines": [
            {
                "product": str(product.pk),
                "quantity": str(qty),
                "unit_cost": str(price),
                "offset_account": str(offset.pk),
            }
            for product, (_desc, qty, price) in zip(products, lines)
        ],
    }
    currency = _currency(reviewed)
    if currency:
        payload["currency"] = currency
    return _run(PurchaseOrderSerializer, payload, request)


APPLIERS = {
    "invoice": apply_invoice,
    "purchase_order": apply_purchase_order,
}


def apply_options(tenant_id):
    """Every choice the Apply form needs, unpaginated. The regular list
    endpoints are capped at PAGE_SIZE with no page_size override, so a
    picker built on them would silently hide the 26th partner/product."""
    def rows(qs, label):
        return [{"id": str(o.pk), "label": label(o)} for o in qs]

    return {
        "partners": [
            {"id": str(p.pk), "label": p.name, "partner_type": p.partner_type}
            for p in Partner.objects.filter(tenant_id=tenant_id, is_active=True).order_by("name")
        ],
        "accounts": [
            {"id": str(a.pk), "label": f"{a.code} {a.name}", "account_type": a.account_type}
            # Header/group accounts are excluded: a draft built on one could
            # never be posted (post_journal_entry refuses NonPostableAccount).
            for a in Account.objects.filter(tenant_id=tenant_id, is_active=True, is_postable=True).order_by("code")
        ],
        "warehouses": rows(
            Warehouse.objects.filter(tenant_id=tenant_id, is_active=True).order_by("name"),
            lambda w: f"{w.code} {w.name}",
        ),
        "products": [
            {"id": str(p.pk), "label": f"{p.internal_ref} {p.name}".strip(), "name": p.name}
            for p in Product.objects.filter(tenant_id=tenant_id, is_active=True).order_by("name")
        ],
    }
