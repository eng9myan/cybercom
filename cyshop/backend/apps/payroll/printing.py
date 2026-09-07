"""Print-ready payslip HTML (browser Ctrl+P -> PDF)."""
from xml.sax.saxutils import escape as e

from django.http import HttpResponse

_CSS = """
* { box-sizing: border-box; }
body { font: 13px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; color: #0f172a;
       margin: 0; padding: 32px; background: #fff; }
.slip { max-width: 620px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 10px; padding: 24px; }
h1 { font-size: 18px; margin: 0 0 4px; }
.muted { color: #64748b; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 24px; margin: 16px 0; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
td { padding: 6px 0; border-bottom: 1px solid #f1f5f9; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.net { border-top: 2px solid #0f172a; font-weight: 700; font-size: 15px; }
@media print { body { padding: 0; } }
"""


def payslip_html(slip) -> str:
    emp = slip.employee
    batch = slip.batch
    gross = slip.gross_salary
    allow = slip.allowances_total or 0
    ded = slip.deductions_total or 0
    net = slip.net_salary
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Payslip {e(str(emp))}</title><style>{_CSS}</style></head><body>
<div class="slip">
  <h1>Payslip</h1>
  <div class="muted">{e(batch.name)} · {batch.period_start} to {batch.period_end}</div>
  <div class="grid">
    <div><span class="muted">Employee</span><br><strong>{e(emp.first_name)} {e(emp.last_name)}</strong></div>
    <div><span class="muted">Employee ID</span><br>{e(emp.employee_id)}</div>
    <div><span class="muted">Job title</span><br>{e(emp.job_title or '—')}</div>
    <div><span class="muted">Working days</span><br>{slip.working_days} (absent {slip.absent_days})</div>
  </div>
  <table>
    <tr><td>Gross salary</td><td class="num">{gross}</td></tr>
    <tr><td>Allowances</td><td class="num">{allow}</td></tr>
    <tr><td>Deductions</td><td class="num">-{ded}</td></tr>
    <tr class="net"><td>Net pay ({e(emp.currency)})</td><td class="num">{net}</td></tr>
  </table>
  <div class="muted" style="font-size:11px">Status: {slip.status}</div>
</div></body></html>"""


def render_payslip(slip):
    return HttpResponse(payslip_html(slip), content_type="text/html")
