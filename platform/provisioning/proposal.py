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
        # "textile" deliberately removed -- textile_manufacturing is a
        # precise dedicated pack now and would otherwise lose to this
        # generic bucket's shorter, more easily-triggered terms.
        ("factory", 3), ("manufactur", 3), ("production", 2), ("bom", 2),
        ("assembly", 2), ("sweets", 2), ("bakery", 2), ("pharma", 2),
        ("furniture", 2), ("plastic", 2), ("chemical", 2), ("plant", 1),
    ],
    "services": [
        # "law firm" / "accounting firm" / "architecture" deliberately live on
        # their own dedicated packs below, not here -- keeping them as generic
        # services signals would mean a description naming the exact business
        # never reaches the more precise pack that exists for it.
        ("consulting", 3), ("agency", 2), ("engineering office", 3),
        ("software company", 2), ("billable", 3), ("timesheet", 2), ("retainer", 2),
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

    # ── Second-batch industry packs (49->66 catalog expansion) ──────────────
    "law_firm": [
        ("law firm", 3), ("lawyer", 3), ("attorney", 3), ("legal practice", 3),
        ("litigation", 3), ("client trust", 2), ("bar association", 2), ("paralegal", 2),
    ],
    "accounting_firm": [
        ("accounting firm", 3), ("audit firm", 3), ("cpa", 3), ("bookkeeping firm", 3),
        ("tax advisory", 2), ("audit opinion", 3), ("assurance services", 2),
    ],
    "marketing_agency": [
        ("marketing agency", 3), ("ad agency", 3), ("advertising agency", 3),
        ("creative agency", 3), ("media buying", 3), ("campaigns", 2), ("brand agency", 2),
    ],
    "it_services": [
        ("it support", 3), ("managed service provider", 3), ("msp", 3), ("it services", 3),
        ("helpdesk", 2), ("sla", 1), ("it consulting", 2), ("network support", 2),
    ],
    "salon_spa": [
        ("salon", 3), ("spa", 3), ("hairdresser", 3), ("barbershop", 3), ("stylist", 2),
        ("nail bar", 2), ("beauty parlour", 2), ("beauty parlor", 2),
    ],
    "gym_fitness": [
        ("gym", 3), ("fitness studio", 3), ("membership club", 2), ("personal training", 2),
        ("crossfit", 2), ("fitness classes", 2),
    ],
    "veterinary": [
        ("veterinary", 3), ("vet clinic", 3), ("animal hospital", 3), ("pet clinic", 3),
        ("vaccinations", 1), ("microchip", 2), ("animal patients", 2),
    ],
    "dental_clinic": [
        ("dental", 3), ("dentist", 3), ("orthodont", 3), ("dental clinic", 3),
        ("teeth", 2), ("dental lab", 2),
    ],
    "coworking": [
        ("coworking", 3), ("shared office", 3), ("hot desk", 3), ("dedicated desk", 2),
        ("meeting rooms", 2), ("flexible workspace", 3),
    ],
    "event_management": [
        ("event management", 3), ("event planner", 3), ("wedding planner", 2),
        ("conference organiser", 2), ("exhibitions", 2), ("run sheet", 2),
    ],
    "catering": [
        ("catering", 3), ("caterer", 3), ("buffet", 2), ("function sheet", 2),
        ("per-head", 2), ("banquet", 2),
    ],
    "bakery": [
        ("bakery", 3), ("baker", 2), ("pastry shop", 2), ("bread production", 2),
        ("cakes", 1), ("baked goods", 2),
    ],
    "florist": [
        ("florist", 3), ("flower shop", 3), ("bouquets", 2), ("floral arrangements", 3),
        ("funeral tributes", 2), ("wedding flowers", 2),
    ],
    "clothing_retail": [
        ("clothing store", 3), ("fashion retail", 3), ("apparel store", 3), ("boutique", 2),
        ("garments store", 2), ("size run", 1),
    ],
    "electronics_retail": [
        ("electronics store", 3), ("gadget shop", 2), ("mobile phone shop", 3),
        ("computer store", 2), ("rma", 2), ("warranty claims", 2),
    ],
    "hardware_store": [
        ("hardware store", 3), ("building supplies", 3), ("trade counter", 3),
        ("timber merchant", 2), ("diy store", 2), ("builders merchant", 3),
    ],
    "furniture_retail": [
        ("furniture store", 3), ("furniture showroom", 3), ("mattress store", 2),
        ("made-to-order furniture", 2), ("sofa", 1),
    ],
    "optical": [
        ("optician", 3), ("optical store", 3), ("eyewear", 3), ("eyeglasses", 2),
        ("sight test", 3), ("prescription lenses", 3),
    ],
    "photography": [
        ("photography studio", 3), ("photographer", 3), ("wedding photography", 2),
        ("photo shoot", 2), ("retoucher", 2),
    ],
    "driving_school": [
        ("driving school", 3), ("driving instructor", 3), ("driving lessons", 3),
        ("learner driver", 2), ("theory test", 2),
    ],
    "training_center": [
        ("training center", 3), ("training centre", 3), ("certification courses", 2),
        ("delegates", 2), ("course provider", 3), ("cohort", 1),
    ],
    "cleaning_services": [
        ("cleaning company", 3), ("commercial cleaning", 3), ("janitorial", 3),
        ("cleaning contract", 2), ("office cleaning", 2), ("cleaning crew", 2),
    ],
    "hvac_services": [
        ("hvac", 3), ("air conditioning contractor", 3), ("refrigeration technician", 2),
        ("heating and cooling", 2), ("ppm visits", 2),
    ],
    "landscaping": [
        ("landscaping", 3), ("grounds maintenance", 3), ("gardening company", 2),
        ("lawn care", 2), ("tree surgeon", 2), ("hard landscaping", 2),
    ],
    "solar_energy": [
        ("solar installer", 3), ("solar panels", 3), ("pv system", 3), ("photovoltaic", 3),
        ("solar energy", 2), ("inverter installation", 2),
    ],
    "equipment_rental": [
        ("equipment rental", 3), ("tool hire", 3), ("plant hire", 3), ("machinery rental", 3),
        ("hire fleet", 2), ("hire desk", 2),
    ],
    "printing": [
        ("print shop", 3), ("printing company", 3), ("signage company", 2),
        ("large format printing", 2), ("press operator", 2), ("litho printing", 2),
    ],
    "metal_fabrication": [
        ("metal fabrication", 3), ("fabrication shop", 3), ("welding shop", 2),
        ("steel fabricator", 3), ("sheet metal", 2), ("structural steel", 2),
    ],
    "food_distribution": [
        ("food distribution", 3), ("food wholesaler", 3), ("cold chain", 3),
        ("frozen food distributor", 2), ("fmcg distributor", 2), ("food depot", 2),
    ],
    "property_management": [
        ("property management", 3), ("letting agency", 3), ("rental portfolio", 3),
        ("landlord statement", 2), ("tenancy agreement", 2), ("rent roll", 2),
    ],
    "auto_service": [
        ("auto repair", 3), ("car workshop", 3), ("mechanic shop", 3), ("mot", 2),
        ("vehicle service", 2), ("repair order", 2),
    ],
    "travel_agency": [
        ("travel agency", 3), ("tour operator", 3), ("booking agency", 2),
        ("flights and hotels", 2), ("itinerary", 2), ("travel consultant", 2),
    ],
    "architecture_firm": [
        ("architecture firm", 3), ("architect", 3), ("architectural practice", 3),
        ("riba stage", 3), ("planning submission", 2), ("design stage", 1),
    ],
    "electrician_services": [
        ("electrical contractor", 3), ("electrician", 3), ("electrical certificate", 3),
        ("eicr", 3), ("wiring", 1), ("electrical safety", 2),
    ],
    "handyman_services": [
        ("handyman", 3), ("home repair", 2), ("odd jobs", 2), ("small repairs", 2),
        ("multi-trade", 2),
    ],
    "surveying_mapping": [
        ("surveying", 3), ("land surveyor", 3), ("topographic survey", 3),
        ("measured building survey", 3), ("boundary survey", 2), ("gis mapping", 2),
    ],
    "corporate_gifts": [
        ("corporate gifts", 3), ("promotional products", 3), ("branded merchandise", 3),
        ("artwork proof", 2), ("moq", 1),
    ],
    "electronics_assembly": [
        ("contract manufacturer", 3), ("pcb assembly", 3), ("electronics assembly", 3),
        ("box build", 2), ("bom", 1), ("first article inspection", 2),
    ],
    "packaging_manufacturing": [
        ("injection moulding", 3), ("plastic manufacturer", 3), ("packaging manufacturer", 3),
        ("blow moulding", 2), ("mould tooling", 2), ("resin", 1),
    ],
    "woodworking_carpentry": [
        ("carpentry", 3), ("joinery", 3), ("cabinetmaker", 3), ("bespoke furniture maker", 2),
        ("fitted wardrobes", 2), ("woodworking shop", 2),
    ],
    "textile_manufacturing": [
        ("garment factory", 3), ("garment manufacturer", 3), ("cut and sew", 3),
        ("textile manufacturer", 3), ("textile manufacturing", 3),
        ("fabric mill", 2), ("cutting plan", 1),
    ],
    "logistics_3pl": [
        ("3pl", 3), ("third-party logistics", 3), ("contract warehousing", 3),
        ("fulfilment provider", 3), ("pick pack ship", 2), ("client-owned inventory", 2),
    ],
    "toy_store": [
        ("toy store", 3), ("toy shop", 3), ("toys retailer", 2), ("children's toys", 2),
    ],
    "bookstore": [
        ("bookstore", 3), ("bookshop", 3), ("book retailer", 2), ("isbn", 2),
    ],
    "cosmetics_store": [
        ("cosmetics store", 3), ("beauty retail", 3), ("makeup shop", 2),
        ("skincare retailer", 2), ("perfume shop", 2),
    ],
    "farm_supply_store": [
        ("farm supply", 3), ("agricultural store", 3), ("feed store", 3),
        ("fertilizer retailer", 2), ("farm inputs", 2),
    ],
    "food_truck": [
        ("food truck", 3), ("mobile food vendor", 3), ("street food van", 2),
        ("food cart", 2),
    ],
    "beverage_distributor": [
        ("beverage distributor", 3), ("drinks wholesaler", 3), ("beverage wholesale", 3),
        ("beverage", 2), ("returnable bottles", 2), ("bottle deposit", 2),
    ],
    "bike_shop": [
        ("bike shop", 3), ("bicycle shop", 3), ("bike mechanic", 2), ("cycle store", 2),
        ("frame number", 1),
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
