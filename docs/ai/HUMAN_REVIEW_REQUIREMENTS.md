# CyAI Human Review Requirements

Status: requirements to implement, cross-referenced against what
`platform/cyai` currently has the *shape* for (InferenceLog has a
`safety_verdict` field) but doesn't yet enforce end-to-end.

## The hard rule

"Healthcare AI must never autonomously diagnose, prescribe, or replace
qualified clinicians" (master spec section 23) is not satisfied by a
guardrail keyword blocklist alone — `GuardrailEngine`'s clinical-safety
check today only blocks configured keywords in the prompt/response text.
That's necessary but not sufficient: a response can avoid every blocked
keyword and still functionally constitute a diagnosis or prescription
instruction.

## What human review actually requires (Tier 3 / CyMed, per
MODEL_RISK_CLASSIFICATION.md)

1. **A review step in the data model, not just a UI convention.** Any
   CyMed model that would receive AI-assisted content (clinical notes,
   coding suggestions, summarizations) needs an explicit
   `ai_generated: bool` + `reviewed_by` + `reviewed_at` set of fields (or
   equivalent) so "a clinician looked at this before it became part of
   the record" is a real, queryable, auditable fact — not something that
   only lived in a UI flow that could be bypassed by calling the API
   directly.
2. **The API layer enforces it, not just the frontend.** If a
   `products.cymed.core.clinical` write endpoint accepts `ai_generated=
   true` content, it must reject the write unless `reviewed_by` is also
   set to a real clinician user_id from the verified JWT — mirrors the
   pattern already used for CyMart's marketplace eligibility checks
   (`Branch.clean()` / `pos.config`'s `_check_marketplace_publication_
   eligibility`) and the order state machine: a business rule enforced in
   the model/service layer, not trusted to the caller.
3. **Reviewer must be qualified for the content type**, not just "any
   authenticated staff." This needs a real role/credential check against
   CyIdentity (`platform.cyidentity.Role`/`RoleAssignment`) — e.g. a
   coding suggestion reviewed by a certified medical coder, a clinical
   summary reviewed by a licensed clinician. Not built — the role
   taxonomy for this doesn't exist yet in `platform.cyidentity` and
   shouldn't be invented ad hoc here.
4. **Break-glass doesn't bypass AI review.** `platform.cyidentity.
   BreakGlassAccess` (emergency access) is about accessing records
   faster, not about skipping the review requirement for AI-generated
   content added during that access.

## Not built, flagged rather than guessed at

The `ai_generated`/`reviewed_by` fields above don't exist on any CyMed
model yet. Adding them means a real migration across whichever CyMed
models are meant to carry AI-assisted content — a decision about exactly
which models (encounters? clinical notes? something new?) needs a product
call, not an assumption made here.
