# CyAI Governance

Status: written against what actually exists in `platform/cyai/` as of
Phase 8, not aspirational. The one load-bearing fact this whole document
hangs on: **`ModelGateway.generate_completion()` is currently simulated,
not a real LLM call** — see the warning added directly in
`platform/cyai/services.py`. Everything below describes the governance
model that has to be in place *before* that's replaced with a real
provider, not a description of AI already running in production.

## What's real today

- `GuardrailPolicy` + `GuardrailEngine.validate_content()` — real regex-
  based PII/PHI scrubbing (email, phone, medical record number patterns)
  and clinical-safety keyword blocking. Runs on both the prompt going in
  and the completion coming out.
- `InferenceLog` — every call (even the simulated ones) is logged with
  tenant_id, prompt, response, token counts, latency, and safety verdict.
  This is the real auditability backbone (see AI_AUDITABILITY.md).
- `RAGService` — also simulated (`# Mimic retrieving semantic context`,
  hardcoded string), same caveat as ModelGateway.

## What's required before any real provider gets wired in

1. **No autonomous clinical decisions, ever.** CyMed AI use cases
   (administrative assistance, medical coding assistance, clinical
   summarization, documentation support — master spec section 23) are
   advisory-only by hard requirement, not a configuration option. A real
   provider integration must never be given the ability to write directly
   to a `products.cymed.core.encounters` / `.clinical` record, issue a
   prescription, or return a response formatted as a diagnosis without a
   clinician confirming it first. This has to be enforced in code (a
   human-approval step before any AI-suggested clinical content is
   persisted), not just policy.
2. **Every real call still goes through GuardrailEngine** — PII/PHI
   scrubbing and clinical-safety blocking don't get bypassed just because
   the model is now real instead of simulated.
3. **Every real call still writes an InferenceLog** — same reasoning.
4. **Model risk classification happens before enabling a use case** — see
   MODEL_RISK_CLASSIFICATION.md. A CyShop demand-forecast suggestion and a
   CyMed clinical summarization are not the same risk tier and shouldn't
   ship under the same review bar.
5. **Provider credentials are real secrets** — API keys for whichever
   provider gets wired in (OpenAI, Anthropic, Gemini, or a self-hosted
   model) go through the same secret management as everything else in
   `docs/security/` — never hardcoded, never logged. `InferenceLog`
   already stores `prompt_used`/`response_text` in the clear, which is
   correct for audit but means the guardrail scrub has to actually run
   first — a bug there is a real PHI leak into the audit log, not a
   theoretical one.

## Recommended real-provider integration path (not built)

Mirrors the payment-provider pattern from Phase 7
(`products/cymart/payments/providers/`): define a `CyAIProvider`
interface, implement one real adapter (Anthropic/OpenAI/Gemini SDK call),
gate it behind a settings flag so the simulated path stays available for
dev/CI without real credentials. Not done in this pass — no real API key
available to build and verify against.
