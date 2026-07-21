# Cymed — Competitive Positioning Analysis (Internal)

**Scope note:** This compares Cymed's real, current architecture (verified against this repo's actual code this session — clinic/hospital/laboratory/pharmacy/imaging department apps, `platform.tenant`/`platform.cyidentity`, `commercial/` licensing) against general knowledge of Oracle Health (Cerner Millennium — PowerChart, CareAware, RadNet, PharmNet, SurgiNet, RevElate), Epic Systems (Chronicles/Resolute), and Hakeem (Saudi MOH's national VistA-derived platform). Specific vendor architecture claims reflect general industry knowledge as of this writing, not a live technical audit of those products — confirm before using externally in a sales context.

## 1. Deployment model and cost structure

Cerner Millennium and Epic are built around a single, monolithic, on-premise-or-managed-hosting database per health system, sold via large multi-year enterprise contracts with substantial implementation-services fees (often exceeding the software license cost itself). Hakeem is a national single-tenant deployment, not a multi-tenant commercial product — it isn't sold at all in the normal sense.

Cymed's real architecture is genuinely different: `platform.tenant` gives every customer an isolated tenant on shared multi-tenant infrastructure (Postgres RLS-scoped `BaseModel`, confirmed this session), provisioned in minutes via `TenantBootstrapService`, not months of professional-services engagement. This is a structural cost and time-to-value advantage worth leading with, not a caveat.

## 2. Modularity and per-department sale

This is Cymed's most concrete, verified differentiator. An architecture audit this session confirmed: `cymed/products/cymed/` has five department packages (clinic, hospital, laboratory, pharmacy, imaging) with **zero lateral cross-imports** between them — each is a horizontal consumer of a shared `core` (patients/encounters/facilities), not of each other. The commercial model already has per-department catalog entries (`ProductCatalogEntry.code` — `cymed_clinic`, `cymed_hospital`, etc.) and per-module licensing (`TenantLicense.module`).

Cerner and Epic both sell as large bundled suites; carving out "just the pharmacy module" as an independently priced, independently deployed product is not how either vendor's commercial model works. Cymed's architecture already supports this natively — the current gap is that licensing isn't yet *enforced* at runtime (an engineering task, not an architecture problem — `has_license()` exists, isn't called anywhere yet). Once wired, "buy just clinic, or just pharmacy, or the full hospital suite" becomes a real, differentiated go-to-market story neither incumbent can easily match.

## 3. Continuity of care vs. standalone sale — the same shared-patient-record tension both incumbents solved

Oracle Health's core pitch (the single unified database driving PowerChart/PharmNet/RadNet/SurgiNet in real time) is architecturally similar to what Cymed already has: all five departments write to the same `core.patients.Patient` and `core.encounters.Encounter`. Cymed doesn't need to build this — it already exists. The work ahead (see the CyID ecosystem plan) is extending that same-patient-record model *across tenant boundaries* — e.g., a patient's clinic visit at Tenant A and pharmacy pickup at Tenant B sharing one identity and one consented view — which neither Cerner nor Epic's single-database model was designed to do (they assume one health system, one database; Cymed's is multi-tenant by design, which is a harder but more market-flexible problem to solve).

## 4. Honest structural weaknesses in Cymed today (real, not incumbent-comparison)

1. **Per-module licensing exists in the data model but isn't enforced** — a clinic-only tenant today still has hospital/lab/pharmacy/imaging code installed and reachable. Real gap, cheap to close (license-gate the URL/permission layer).
2. **No real-time device/IoT integration** — Cerner's CareAware (bedside monitor/IV pump streaming) has no Cymed equivalent yet. Deliberately deferred (see CyID ecosystem plan Phase 10) — designing the ingestion seam now, not building against hardware that isn't available to test.
3. **No cross-tenant identity yet** — a patient today is scoped to one tenant's `Patient` row; there's no single identity spanning a visit to Tenant A's clinic and Tenant B's pharmacy. This is the actual gap the CyID initiative closes.
4. **FHIR is directional, not standards-complete** — `core/clinical`, `core/orders`, `core/documents`, `core/careplans` are FHIR-*shaped* (Condition/Observation/CarePlan-style vocab) but not `fhir.resources`-typed or serialized to real FHIR JSON; pharmacy has FHIR reference-ID tagging (`fhir_medication_request_id` etc.) but not full resource generation. Real interoperability claims (FHIR R4 conformance testing, national HIE integration) need this closed before being made externally.

## 5. Where Cymed should invest next (roadmap, not yet built)

- **Enforce the existing per-module licensing** — closes the single biggest go-to-market gap (standalone department sales) with the least engineering work, since the data model is already there.
- **CyID cross-tenant identity** — see the dedicated CyID Ecosystem plan (this session) for the phased build. This is the feature that would let Cymed credibly claim "one patient record across every provider in the network," matching Oracle Health's core pitch but across independently-owned tenants instead of one health system's single database.
- **Multi-country billing** (Jordan/Saudi/UAE/USA) — neither Cerner nor Epic's billing (built around US UB-04/CMS-1500 claim forms) travels well internationally without a large localization effort; a jurisdiction-pluggable billing core from day one (also in the CyID plan) is a real structural advantage for GCC/Levant expansion specifically.
