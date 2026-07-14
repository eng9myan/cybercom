# CyAI Model Risk Classification

Status: a classification framework to apply once real providers exist,
not a record of models already deployed (none are — see AI_GOVERNANCE.md).

## Tiers

**Tier 1 — Advisory, non-clinical, reversible.** Output is a suggestion a
human reviews before it has any effect, and a wrong answer costs
inconvenience, not safety or money directly.
- CyShop: demand forecasts, promotion insights, product recommendations.
- CyCom: report explanations, document assistance.
- CyMart: search ranking, merchant insights.
- CyDrive: ETA prediction, driver workload balancing suggestions.
Review bar: guardrail scrub + InferenceLog. No additional sign-off
required before use, but output must be visibly labeled as AI-generated
in any UI that shows it.

**Tier 2 — Advisory, financial or operational impact.** Wrong output
could cause a real financial loss or operational failure if acted on
without review.
- CyMart: fraud signals, demand forecasting feeding into inventory
  commitments.
- CyDrive: automatic dispatch recommendations (the actual dispatch
  decision in `products.cydrive.fleet.services.DispatchEngine` is
  deterministic rule-based code today, not AI — if AI-assisted dispatch
  scoring is added later, it lands in this tier).
Review bar: Tier 1 requirements, plus the consuming code must treat the
AI output as one input to a decision, never the sole trigger for an
automated action with financial consequences (e.g., auto-charging a
customer, auto-terminating a merchant).

**Tier 3 — Clinical, human-in-the-loop mandatory.** CyMed use cases:
administrative assistance, medical coding assistance, clinical
summarization, appointment optimization, documentation support (master
spec section 23's exact CyMed list).
Review bar: Tier 1+2 requirements, plus:
- Output must never be auto-persisted to a clinical record
  (`products.cymed.core.*`, `products.cymed.hospital.*`, etc.) — a
  clinician has to explicitly accept it first.
- Output must never be formatted or presented as a diagnosis or
  prescription decision.
- Every Tier 3 inference is subject to HUMAN_REVIEW_REQUIREMENTS.md
  without exception, including in dev/demo environments — no "it's just
  a demo" carve-out for clinical safety review, since demo data has a way
  of becoming production habits.

## Applying this

Before wiring in a real provider for any given use case, classify it
using this table and confirm the review bar for that tier is actually
implemented in code (not just documented) before it ships.
