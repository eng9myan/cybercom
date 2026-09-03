"""
AI-guided configuration — propose an industry template + department packs
from a natural-language company description.

Two layers:
  1. `propose()` — deterministic keyword/signal scorer against the live
     catalog. Always works, offline, explainable (per-template evidence).
  2. The cyai LLM can later re-rank / enrich this proposal; the response
     shape already carries `rationale` + `evidence` so the UI needs no
     change when that lands.

The scorer favours precision over cleverness: distinctive domain terms map
to one industry; generic ERP words are ignored.
"""

from __future__ import annotations

import re

from platform.provisioning.models import DepartmentPack, IndustryTemplate

# Distinctive signals per industry key. Weighted: strong terms 3, medium 2, weak 1.
INDUSTRY_SIGNALS: dict[str, list[tuple[str, int]]] = {
    "construction": [
        ("construction", 3), ("contractor", 3), ("boq", 3), ("bill of quantities", 3),
        ("site", 1), ("subcontractor", 3), ("tender", 2), ("retention", 2),
        ("project", 1), ("civil", 2), ("mep", 2),
    ],
    "trading": [
        ("trading", 3), ("distribution", 3), ("wholesale", 3), ("distributor", 3),
        ("van sales", 3), ("routes", 2), ("import", 1), ("resell", 2), ("fmcg", 3),
    ],
    "manufacturing": [
        ("factory", 3), ("manufactur", 3), ("production", 2), ("bom", 2),
        ("assembly", 2), ("sweets", 2), ("bakery", 2), ("pharma", 2),
        ("furniture", 2), ("textile", 2), ("plastic", 2), ("chemical", 2), ("plant", 1),
    ],
    "services": [
        ("consulting", 3), ("law firm", 3), ("accounting firm", 3), ("agency", 2),
        ("engineering office", 3), ("software company", 2), ("billable", 3),
        ("timesheet", 2), ("retainer", 3), ("architecture", 2),
    ],
    "logistics": [
        ("logistics", 3), ("transport", 3), ("fleet", 2), ("shipping", 2),
        ("freight", 3), ("trucks", 2), ("delivery company", 3), ("last mile", 3),
        ("dispatch", 2),
    ],
    "realestate": [
        ("real estate", 3), ("property", 3), ("tenants", 3), ("lease", 3),
        ("rent", 2), ("buildings", 1), ("units", 1), ("landlord", 3),
    ],
    "facility": [
        ("facility management", 3), ("facilities", 2), ("hvac", 2), ("cleaning", 2),
        ("work orders", 2), ("sla", 2), ("preventive maintenance", 2), ("technicians", 1),
    ],
    "education": [
        ("school", 3), ("university", 3), ("academy", 3), ("training center", 3),
        ("students", 3), ("tuition", 3), ("classes", 1), ("teachers", 2),
    ],
    "retailgroup": [
        ("retail", 3), ("branches", 1), ("pos", 3), ("stores", 2), ("supermarket", 3),
        ("cashier", 2), ("e-commerce", 2), ("online sales", 2), ("loyalty", 2),
        ("talabat", 2), ("delivery platforms", 2), ("shops", 2),
    ],
    "healthcare": [
        ("hospital", 3), ("clinic", 3), ("medical", 2), ("healthcare", 3),
        ("biomedical", 3), ("medical supplies", 3),
    ],
    "nonprofit": [
        ("ngo", 3), ("nonprofit", 3), ("non-profit", 3), ("charity", 3),
        ("donor", 3), ("grants", 3), ("beneficiar", 3), ("humanitarian", 3),
    ],
}

# Ops keywords → extra department packs beyond the industry's defaults.
OPS_PACK_SIGNALS: list[tuple[str, str]] = [
    (r"\bpos\b|retail|cashier|checkout|shops?\b|branches|online sales|e-?commerce|delivery platform", "pos"),
    (r"factory|manufactur|production", "manufacturing"),
    (r"maintenance|equipment|assets|workshop", "maintenance"),
    (r"document|contract management|knowledge", "documents"),
    (r"sales team|crm|customers|quotation", "sales"),
    (r"warehouse|inventory|stock", "inventory"),
    (r"project", "projects"),
]


def propose(description: str) -> dict:
    text = description.lower()

    scores: dict[str, tuple[int, list[str]]] = {}
    for key, signals in INDUSTRY_SIGNALS.items():
        score = 0
        evidence: list[str] = []
        for term, weight in signals:
            if term in text:
                score += weight
                evidence.append(term)
        if score:
            scores[key] = (score, evidence)

    if not scores:
        return {
            "matched": False,
            "message": "Could not confidently match an industry — pick one manually or add more detail (what the company makes, sells, or operates).",
            "candidates": [],
        }

    ranked = sorted(scores.items(), key=lambda kv: kv[1][0], reverse=True)
    best_key, (best_score, best_evidence) = ranked[0]

    template = (
        IndustryTemplate.objects.filter(key=best_key, is_active=True)
        .order_by("-version")
        .first()
    )
    if not template:
        return {"matched": False, "message": f"Matched '{best_key}' but no active template exists.", "candidates": []}

    # Extra dept packs implied by the description beyond the template defaults.
    extra_packs: list[str] = []
    existing = set(template.department_pack_keys)
    valid_keys = set(DepartmentPack.objects.filter(is_active=True).values_list("key", flat=True))
    for pattern, pack_key in OPS_PACK_SIGNALS:
        if pack_key in valid_keys and pack_key not in existing and re.search(pattern, text):
            if pack_key not in extra_packs:
                extra_packs.append(pack_key)

    runners_up = [
        {"industry_key": k, "score": s, "evidence": ev}
        for k, (s, ev) in ranked[1:4]
    ]

    return {
        "matched": True,
        "industry_key": best_key,
        "industry_name": template.name,
        "template_version": template.version,
        "confidence": "high" if best_score >= 5 else "medium" if best_score >= 3 else "low",
        "evidence": best_evidence,
        "department_packs": list(template.department_pack_keys),
        "extra_department_packs": extra_packs,
        "approval_matrix": template.approval_matrix,
        "import_templates": template.import_templates,
        "rationale": (
            f"Matched '{template.name}' from: {', '.join(best_evidence)}. "
            + (f"Description also suggests adding: {', '.join(extra_packs)}." if extra_packs else "")
        ).strip(),
        "candidates": runners_up,
    }
