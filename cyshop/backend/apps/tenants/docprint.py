"""Shared print-ready HTML for business documents (Ctrl+P -> PDF, no PDF lib).

`document_html()` lays out a header (issuer + doc meta), an optional counter-party
box, a line-item table and a totals stack. Callers pass plain dicts/strings so the
same layout serves purchase orders, quotations and receipts.
"""
from xml.sax.saxutils import escape as _e

from django.http import HttpResponse

_RTL_COUNTRIES = {"SA", "JO", "AE", "EG", "QA", "KW", "BH", "OM", "IQ", "LB", "PS"}

_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font: 13px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; color: #0f172a;
       margin: 0; padding: 32px; background: #fff; }
.doc { max-width: 780px; margin: 0 auto; }
h1 { font-size: 20px; margin: 0 0 2px; }
.muted { color: #64748b; }
.row { display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
.box { border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; }
table { width: 100%; border-collapse: collapse; margin: 18px 0; }
th, td { text-align: start; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }
th { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: #64748b; }
td.num, th.num { text-align: end; font-variant-numeric: tabular-nums; }
.totals { margin-inline-start: auto; width: 280px; }
.totals .row { padding: 4px 0; }
.totals .grand { border-top: 2px solid #0f172a; font-weight: 700; font-size: 15px; padding-top: 6px; }
.note { margin-top: 16px; white-space: pre-wrap; }
.warn { background: #fffbeb; border: 1px solid #fde68a; color: #92400e;
        border-radius: 8px; padding: 8px 12px; margin-top: 16px; font-size: 12px; }
[dir="rtl"] { direction: rtl; }
@media print { body { padding: 0; } .noprint { display: none; } }
"""


def document_html(*, title, doc_meta, issuer, party=None, party_label="",
                  columns, rows, totals, note="", country_code="SA", warnings=None):
    """
    doc_meta / issuer / party: list of (label, value) pairs (value already str)
    columns: list of (header, is_numeric)
    rows:    list of lists (cells, already str), aligned to columns
    totals:  list of (label, value, is_grand)
    """
    rtl = (country_code or "SA").upper() in _RTL_COUNTRIES
    meta_html = " · ".join(_e(str(v)) for _, v in doc_meta if v not in (None, ""))
    issuer_html = "<br>".join(
        f"<span class='muted'>{_e(l)}:</span> {_e(str(v))}" if l else f"<strong>{_e(str(v))}</strong>"
        for l, v in issuer if v not in (None, ""))
    party_html = ""
    if party:
        inner = "<br>".join(
            f"<span class='muted'>{_e(l)}:</span> {_e(str(v))}" if l else f"<strong>{_e(str(v))}</strong>"
            for l, v in party if v not in (None, ""))
        party_html = (f"<div class='box' style='margin-top:16px'>"
                      f"<span class='muted'>{_e(party_label)}</span><br>{inner}</div>")
    head_cells = "".join(
        f"<th class='num'>{_e(h)}</th>" if num else f"<th>{_e(h)}</th>" for h, num in columns)
    body_rows = ""
    for r in rows:
        cells = "".join(
            f"<td class='num'>{_e(str(c))}</td>" if columns[i][1] else f"<td>{_e(str(c))}</td>"
            for i, c in enumerate(r))
        body_rows += f"<tr>{cells}</tr>"
    totals_html = "".join(
        f"<div class='row{' grand' if g else ''}'><span>{_e(l)}</span><span>{_e(str(v))}</span></div>"
        for l, v, g in totals)
    warn_html = ""
    if warnings:
        warn_html = "<div class='warn'>" + "<br>".join(_e(w) for w in warnings) + "</div>"
    note_html = f"<div class='note muted'>{_e(note)}</div>" if note else ""

    return f"""<!doctype html><html{' dir="rtl"' if rtl else ''}><head>
<meta charset="utf-8"><title>{_e(title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap">
<style>{_CSS}{"body{font-family:'Cairo',sans-serif;}" if rtl else ""}</style></head>
<body><div class="doc">
  <div class="row">
    <div><h1>{_e(title)}</h1><div class="muted">{meta_html}</div></div>
    <div class="box">{issuer_html}</div>
  </div>
  {party_html}
  <table>
    <thead><tr>{head_cells}</tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
  <div class="totals">{totals_html}</div>
  {note_html}
  {warn_html}
</div></body></html>"""


def html_response(html):
    return HttpResponse(html, content_type="text/html")
