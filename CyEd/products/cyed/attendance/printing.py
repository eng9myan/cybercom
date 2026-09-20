"""
Late-arrival pass — print-ready HTML (Ctrl+P -> PDF, no PDF library needed).
Same convention CyCom uses for purchase orders: a small self-contained
HTML document with print CSS, not a generated-and-stored PDF — a late pass
has no accounting/statutory retention need, so there's nothing to gain from
persisting bytes the way a report card does.
"""
from xml.sax.saxutils import escape as _e

from django.http import HttpResponse

_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font: 13px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; color: #0f172a;
       margin: 0; padding: 32px; background: #fff; }
.slip { max-width: 380px; margin: 0 auto; border: 2px dashed #94a3b8; border-radius: 10px; padding: 20px; }
h1 { font-size: 16px; margin: 0 0 2px; text-transform: uppercase; letter-spacing: .06em; }
.muted { color: #64748b; }
.pass-number { font-family: ui-monospace, monospace; font-size: 13px; color: #64748b; margin-bottom: 12px; }
table { width: 100%; border-collapse: collapse; margin: 14px 0; }
td { padding: 6px 0; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
td.label { color: #64748b; width: 40%; }
.signoff { margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 11px; color: #64748b; }
@media print { body { padding: 0; } .noprint { display: none; } }
"""


def late_pass_html(late_pass) -> str:
    student = late_pass.student
    rows = [
        ("Student", f"{student.first_name} {student.last_name}"),
        ("Year", str(getattr(student, "year_level", "") or "")),
        ("Date", late_pass.arrival_date.isoformat()),
        ("Arrival time", late_pass.arrival_time.strftime("%H:%M")),
        ("Reason", late_pass.get_reason_display()),
        ("Heading to", late_pass.class_section.name if late_pass.class_section else "—"),
        ("Issued by", late_pass.issued_by or "—"),
    ]
    if late_pass.reason_detail:
        rows.append(("Notes", late_pass.reason_detail))

    row_html = "".join(
        f"<tr><td class='label'>{_e(l)}</td><td>{_e(str(v))}</td></tr>" for l, v in rows
    )

    return f"""<!doctype html><html><head>
<meta charset="utf-8"><title>Late Pass {_e(late_pass.pass_number)}</title>
<style>{_CSS}</style></head>
<body><div class="slip">
  <h1>Late Arrival Pass</h1>
  <div class="pass-number">{_e(late_pass.pass_number)}</div>
  <table>{row_html}</table>
  <div class="signoff">Please present this pass to your classroom teacher on arrival.</div>
</div></body></html>"""


def render_late_pass(late_pass) -> HttpResponse:
    return HttpResponse(late_pass_html(late_pass), content_type="text/html")
