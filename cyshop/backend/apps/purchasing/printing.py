"""Print-ready purchase order (Ctrl+P -> PDF)."""
from apps.tenants.docprint import document_html, html_response


def _f(v):
    return f"{float(v or 0):,.2f}"


def purchase_order_html(po):
    company = po.company
    vendor = po.vendor
    cur = po.currency
    lines = po.lines.filter(is_deleted=False).select_related("product")
    rows = [
        [ln.product.name, _f(ln.quantity), _f(ln.unit_cost),
         f"{float(ln.tax_rate or 0) * 100:.0f}%", _f(ln.line_subtotal)]
        for ln in lines
    ]
    return document_html(
        title="Purchase Order",
        doc_meta=[("#", po.po_number), ("Date", po.order_date),
                  ("Expected", po.expected_date), ("Status", po.get_status_display())],
        issuer=[("", company.name),
                ("Branch", getattr(po.branch, "name", None)),
                ("Warehouse", getattr(po.warehouse, "name", None))],
        party=[("", vendor.name),
               ("Contact", getattr(vendor, "contact_name", "") or None),
               ("Email", getattr(vendor, "email", "") or None),
               ("Phone", getattr(vendor, "phone", "") or None)],
        party_label="Vendor",
        columns=[("Item", False), ("Qty", True), ("Unit cost", True),
                 ("Tax", True), (f"Amount ({cur})", True)],
        rows=rows,
        totals=[("Subtotal", f"{_f(po.subtotal)} {cur}", False),
                ("Tax", f"{_f(po.tax_amount)} {cur}", False),
                ("Total", f"{_f(po.total)} {cur}", True)],
        note=po.notes or "",
        country_code=getattr(company, "country_code", "SA"),
    )


def render_purchase_order(po):
    return html_response(purchase_order_html(po))
