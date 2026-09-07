"""Print-ready HTML for a tax invoice (browser Ctrl+P -> PDF). No PDF library."""
import io
from xml.sax.saxutils import escape as e

import segno
from django.http import HttpResponse


def _qr_svg(payload: str) -> str:
    buf = io.BytesIO()
    segno.make(payload, error="m").save(buf, kind="svg", scale=3, border=1,
                                        dark="#0f172a", light=None, xmldecl=False)
    return buf.getvalue().decode("utf-8")


_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font: 13px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; color: #0f172a;
       margin: 0; padding: 32px; background: #fff; }
.doc { max-width: 780px; margin: 0 auto; }
h1 { font-size: 20px; margin: 0 0 2px; }
.muted { color: #64748b; }
.row { display: flex; justify-content: space-between; gap: 24px; }
.box { border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; }
table { width: 100%; border-collapse: collapse; margin: 18px 0; }
th, td { text-align: start; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }
th { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: #64748b; }
td.num, th.num { text-align: end; font-variant-numeric: tabular-nums; }
.totals { margin-inline-start: auto; width: 280px; }
.totals .row { padding: 4px 0; }
.totals .grand { border-top: 2px solid #0f172a; font-weight: 700; font-size: 15px; padding-top: 6px; }
.qr { text-align: center; margin-top: 20px; }
.qr svg { width: 130px; height: 130px; }
.warn { background: #fffbeb; border: 1px solid #fde68a; color: #92400e;
        border-radius: 8px; padding: 8px 12px; margin-top: 16px; font-size: 12px; }
[dir="rtl"] { direction: rtl; }
@media print { body { padding: 0; } .noprint { display: none; } }
"""


def invoice_html(invoice, doc, profile) -> str:
    rtl = (profile.country_code or "SA") in ("SA", "JO", "AE", "EG", "QA", "KW", "BH", "OM")
    seller = profile.legal_name_ar if (rtl and profile.legal_name_ar) else profile.legal_name
    type_label = {"standard": "Tax Invoice", "simplified": "Simplified Tax Invoice",
                  "credit_note": "Credit Note", "debit_note": "Debit Note"}.get(
        invoice.invoice_type, "Invoice")
    lines = "".join(
        f"<tr><td>{e(l.description)}</td><td class='num'>{l.quantity}</td>"
        f"<td class='num'>{l.unit_price}</td><td class='num'>{(l.tax_rate*100):.0f}%</td>"
        f"<td class='num'>{l.line_total}</td></tr>"
        for l in invoice.lines.filter(is_deleted=False).order_by("line_no")
    )
    qr = _qr_svg(doc.qr_code) if doc and doc.qr_code else ""
    warn = ""
    if doc and doc.warnings:
        warn = "<div class='warn'>" + "<br>".join(e(w) for w in doc.warnings) + "</div>"
    cur = invoice.currency
    return f"""<!doctype html><html{' dir="rtl"' if rtl else ''}><head>
<meta charset="utf-8"><title>{e(invoice.number)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap">
<style>{_CSS}{"body{font-family:'Cairo',sans-serif;}" if rtl else ""}</style></head>
<body><div class="doc">
  <div class="row">
    <div><h1>{e(type_label)}</h1><div class="muted">#{e(invoice.number)} · {invoice.issue_date}</div></div>
    <div class="box">
      <strong>{e(seller or invoice.company.name)}</strong><br>
      <span class="muted">VAT: {e(profile.vat_number or '—')}</span><br>
      <span class="muted">{e(profile.address_city)} {e(profile.country_code)}</span>
    </div>
  </div>
  <div class="box" style="margin-top:16px">
    <span class="muted">Bill to</span><br><strong>{e(invoice.customer_name)}</strong>
    {(' · VAT ' + e(invoice.customer_tax_number)) if invoice.customer_tax_number else ''}
  </div>
  <table>
    <thead><tr><th>Description</th><th class="num">Qty</th><th class="num">Unit</th>
      <th class="num">VAT</th><th class="num">Amount ({cur})</th></tr></thead>
    <tbody>{lines}</tbody>
  </table>
  <div class="totals">
    <div class="row"><span>Subtotal</span><span>{invoice.subtotal} {cur}</span></div>
    <div class="row"><span>VAT</span><span>{invoice.tax_total} {cur}</span></div>
    <div class="row grand"><span>Total</span><span>{invoice.total} {cur}</span></div>
  </div>
  <div class="qr">{qr}<div class="muted" style="font-size:11px">Scan to verify</div></div>
  {warn}
</div></body></html>"""


def render_invoice(invoice):
    from . import services
    doc = getattr(invoice, "einvoice", None)
    if not doc:
        doc = services.generate(invoice)
    profile = getattr(invoice.company, "tax_profile", None)
    if profile is None:
        from .models import TaxProfile
        profile = TaxProfile(company=invoice.company, legal_name=invoice.company.name,
                             country_code=getattr(invoice.company, "country_code", "SA"))
    return HttpResponse(invoice_html(invoice, doc, profile), content_type="text/html")
