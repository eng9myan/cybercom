# CyAI Auditability

Status: describes what `InferenceLog` actually captures today, verified
against `platform/cyai/models.py` and `services.py`, plus gaps.

## What's captured today (real)

Every `ModelGateway.generate_completion()` call — including the currently
-simulated ones — writes an `InferenceLog` row with:
- `tenant_id`
- `model` (FK to `ModelConfig` — provider + model name)
- `prompt_used` (post-guardrail-scrub prompt, so PII/PHI patterns matched
  by `GuardrailEngine` are already redacted before storage)
- `response_text` (post-guardrail-scrub response)
- `tokens_prompt` / `tokens_completion` (currently `len(text) // 4` — a
  rough estimate, not a real tokenizer count; fine for the simulated
  responses, needs a real tokenizer once a real provider is wired in,
  since billing and rate limits depend on accurate counts)
- `latency_ms`
- `safety_verdict` (`passed` / `flagged` / `blocked`)
- `error_message`

This satisfies "every sensitive operation gets an audit record" for AI
calls specifically. It does **not** yet satisfy "who reviewed
AI-generated content before it was used" — see HUMAN_REVIEW_REQUIREMENTS.md,
that's a separate, unbuilt piece.

## Gaps (verified, not assumed)

1. **No correlation_id / causation_id / trace_id on InferenceLog**,
   matching the exact same gap already documented in
   `docs/api/EVENT_SCHEMA_STANDARDS.md` for `OutboxEvent`. An
   InferenceLog row currently can't be reliably tied back to the specific
   user action or order/encounter that triggered it except via whatever
   the caller chose to put in the prompt text — not a real foreign key or
   indexed field.
2. **No `platform.audit` cross-reference.** `platform.audit` (Phase 1)
   is the general-purpose audit trail for sensitive operations across the
   whole platform; `InferenceLog` is a separate, AI-specific table that
   doesn't currently also emit a `platform.audit` entry. For Tier 3
   (clinical) AI use per MODEL_RISK_CLASSIFICATION.md, an AI-assisted
   clinical suggestion probably needs to show up in both — the CyMed-
   specific inference log AND the general tamper-evident audit trail
   that a hospital compliance officer would search — not built.
3. **Guardrail scrub happening before storage is good, but there's no
   verification that it actually caught everything.** `GuardrailEngine`'s
   PII/PHI patterns are a fixed regex set (email, phone, MRN). Nothing
   validates that a real clinical AI response doesn't contain PHI in a
   form those three patterns don't catch (a patient's name and diagnosis
   in prose, for instance) — expanding that pattern set, or replacing it
   with a real PHI-detection library, is real follow-up work before any
   Tier 3 use case goes live with a real provider.

## Once a real provider is wired in

Add: correlation/causation/trace IDs (matching whatever fix eventually
lands for `OutboxEvent`, ideally the same convention), a real tokenizer
per provider, and the `platform.audit` cross-post for Tier 2+ inferences.
