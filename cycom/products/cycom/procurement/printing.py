"""Print-ready purchase order (Ctrl+P -> PDF). Ported from cyshop's
apps/purchasing/printing.py, adapted to CyCom's leaner PurchaseOrder model
(no po_number/order_date/notes/tax_rate — single-company-per-tenant, so the
issuer box reads the Tenant's own name/country instead of a Company FK)."""

from products.cycom.procurement.docprint import document_html, html_response


def _f(v):
    return f"{float(v or 0):,.2f}"


def purchase_order_html(po):
    from platform.tenant.models import Tenant

    tenant = Tenant.objects.filter(id=po.tenant_id).first()
    vendor = po.vendor
    cur = po.currency
    lines = po.lines.all().select_related("product")
    rows = [
        [ln.product.name, _f(ln.quantity), _f(ln.unit_cost), _f(ln.quantity * ln.unit_cost)]
        for ln in lines
    ]
    total = po.total_amount
    return document_html(
        title="Purchase Order",
        doc_meta=[
            ("#", f"PO-{str(po.id)[:8].upper()}"),
            ("Date", po.created_at.date().isoformat()),
            ("Status", po.get_status_display()),
        ],
        issuer=[("", tenant.name if tenant else ""), ("Warehouse", getattr(po.warehouse, "name", None))],
        party=[
            ("", vendor.name),
            ("Contact", vendor.contact_name or None),
            ("Email", vendor.email or None),
            ("Phone", vendor.phone or None),
        ],
        party_label="Vendor",
        columns=[("Item", False), ("Qty", True), ("Unit cost", True), (f"Amount ({cur})", True)],
        rows=rows,
        totals=[("Total", f"{_f(total)} {cur}", True)],
        country_code=tenant.country_code if tenant else "SA",
    )


def render_purchase_order(po):
    return html_response(purchase_order_html(po))
