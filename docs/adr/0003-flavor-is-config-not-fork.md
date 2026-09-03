# ADR-0003: A vertical flavor is config + a thin pack, never a code fork

- **Status:** Accepted
- **Date:** 2026-09-04
- **Deciders:** CDAC (to ratify)
- **Related:** blueprint `A`, `C.3`, `E.5`, `F.1`, `J.1 A5`; `M_risk_register.md` R04

## Context

The strategy is "build the core once, express every industry as a flavor." This only pays off
if a new vertical is genuinely cheap — weeks, not a fork. The failure mode is silent: flavors
accrete bespoke models and frontends until the codebase is three products' worth of
maintenance again (exactly the state we're consolidating out of).

## Decision

We will define a **flavor** as a declarative, versioned package:

- module set (which core services are enabled)
- `catalog_profile` / entity `attributes` profiles (typed extension fields — **no new
  top-level models** without CDAC review of an extension table)
- layout templates (design-system slots — **no bespoke frontend code**)
- tax / regulatory presets (config, not code branches)
- workflows (composed from core primitives)
- KPI dashboard pack, seed data, required integrations

A tenant can have **multiple flavors** composed (e.g. clinic + retail pharmacy).

Every flavor release passes the **"thin flavor" checklist** (`F.1`) as a hard gate. CDAC's
flavor board may grant a **time-boxed** exception; a permanent core change requires an ADR.

## Consequences

- Positive: new verticals ship in weeks; one core stays the single thing to secure, certify,
  localise, and upgrade; the consolidation doesn't silently reverse.
- Negative / trade-offs: some verticals will strain the model; contributors must resist the
  quick fork and route real gaps through CDAC — enforced by the release gate + `CODEOWNERS`.
- Follow-up: build the flavor engine (`platform/provisioning` promotion); `flavor.schema.yaml`
  + validator in CI; thin-flavor checklist automated where possible.
- Revisit if: ≥ 2 target verticals genuinely cannot be expressed within the model — then the
  model is extended for all, not forked for one.
