# ADR-0002: Modular monolith with selective service carve-outs, not microservices-first

- **Status:** Accepted
- **Date:** 2026-09-04
- **Deciders:** CDAC (to ratify)
- **Related:** blueprint `C.0`, `C.6`, `J.1 A4`; `M_risk_register.md` R07/R15

## Context

The ecosystem spans commerce, health, finance, HR, scheduling, analytics, integrations. The
temptation is a microservices architecture per domain. But: the delivery team is small
(`BUSINESS_PLAN.md` risk); the existing code is one Django project + shared `platform/`;
premature service sprawl multiplies operational surface, distributed-transaction complexity,
and local-dev friction — a common cause of stalled platform rebuilds.

## Decision

We will ship the core as a **modular monolith**: Django apps with clean, event-mediated
boundaries behind one API gateway, one deployable core. We carve out an independent service
**only** when a concrete driver exists — independent scaling profile, hard compliance
isolation, or a dedicated owning team.

Day-1 carve-outs (each has a driver): **Identity** (security isolation, reused by all),
**Payments/Billing** (PCI scope isolation), **Search/Analytics read-model** (scaling
profile), **Async workers** (scaling profile), **File/Media / CyVault** (scaling + already
separate). Everything else stays in the core until a driver appears.

## Consequences

- Positive: fast local dev, simple deploys, transactional integrity within the core, low ops
  burden for a small team; carve-out stays cheap because boundaries + events exist from day one.
- Negative / trade-offs: the core is one scaling + release unit for most domains; a hot domain
  can force an unplanned carve-out (R15) — acceptable because the boundary work is already done.
- Follow-up: enforce app-boundary discipline (no cross-app model imports; interact via
  services + events); `CODEOWNERS` per app; document the carve-out criteria in the runbook.
- Revisit if: the team grows past ~5 independent pods, or a domain provably needs its own
  release cadence.
