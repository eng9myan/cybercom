"""Denial → appeal letter composer.

Uses payer denial codes + clinical documentation to draft an appeal letter.
Baseline: template + variable substitution. Upgrade: LLM-based generation.
"""
from __future__ import annotations

from django.template import Context, Template


APPEAL_TEMPLATE = """
<h3>Appeal — Claim {{ claim_number }}</h3>
<p><strong>Patient:</strong> {{ patient_id }}<br>
<strong>Date of Service:</strong> {{ dos }}<br>
<strong>Payer:</strong> {{ payer }}<br>
<strong>Original Charge:</strong> SAR {{ charge_total }}</p>

<h4>Denial reason(s)</h4>
<ul>
{% for d in denial_codes %}
  <li><strong>{{ d.carc }}</strong>: {{ d.note }}</li>
{% endfor %}
</ul>

<h4>Grounds for appeal</h4>
<p>{{ narrative }}</p>

<h4>Supporting documentation</h4>
<ul>
{% for doc in supporting_docs %}
  <li>{{ doc.name }}</li>
{% endfor %}
</ul>

<p>We respectfully request reconsideration of this claim per §{{ policy_clause }}
of the payer contract and the enclosed clinical documentation.</p>

<p>{{ prepared_by }} · {{ prepared_at }}</p>
"""


class AppealComposer:
    def compose(self, *, claim, denial_codes: list[dict],
                narrative: str, supporting_docs: list[dict] | None = None,
                prepared_by: str = "CyMed RCM") -> str:
        from django.utils import timezone
        ctx = {
            "claim_number": claim.claim_number,
            "patient_id": str(claim.patient_profile_id),
            "dos": str(claim.created_at.date()),
            "payer": claim.payer_code,
            "charge_total": str(claim.charge_total),
            "denial_codes": denial_codes,
            "narrative": narrative,
            "supporting_docs": supporting_docs or [],
            "policy_clause": "4.2 (Reconsideration)",
            "prepared_by": prepared_by,
            "prepared_at": timezone.now().strftime("%Y-%m-%d %H:%M"),
        }
        return Template(APPEAL_TEMPLATE).render(Context(ctx))
