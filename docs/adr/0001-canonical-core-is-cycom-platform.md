# ADR-0001: Canonical core = CyCom + `platform/`; CyShop migrates in and is archived

- **Status:** Accepted
- **Date:** 2026-09-04
- **Deciders:** CDAC (to ratify at first session)
- **Related:** blueprint `A`, `D.3`, `J.1 A3`; `SYSTEM_INVENTORY.md`; `M_risk_register.md` R01/R09

## Context

Three products overlap heavily:

- **CyShop** (~7k Py LOC, 12 apps, 0 test files) has its own JWT auth, own `tenants`,
  `identity`, `accounting`, `hr`, `payroll`, `inventory` — it does **not** sit on the shared
  `platform/`. A 2026-08 audit found it ~90% duplicate of CyCom. Its unique value (catalog,
  POS Device/receipt/KDS, quotations, onboarding UX) has already been ported into CyCom.
- **CyCom** (~15k Py LOC, 39 apps, tested, several flows live-verified) is built on the shared
  `platform/` core (identity, tenant, provisioning, events, audit, notifications).
- **CyMed** (16 apps) already sits correctly on the same `platform/` — proof the shared-core
  model works for a vertical.

Maintaining CyShop separately is duplicated cost with no offsetting benefit. Cross-domain
workflows, unified compliance (ZATCA, PDPL, payroll), and one identity fabric all require a
single core.

## Decision

We will treat **CyCom + `platform/` as the canonical core and target data model**. CyShop
migrates into it fully (per the `D.3` playbook) and is then archived (repo + DB snapshot
retained one year). CyMed keeps its clinical apps but re-homes its shared concerns (identity,
tenant, billing, catalog/pharmacy, inventory, finance, HR) onto the canonical core; its
clinical apps become HealthFlavour modules.

Retail becomes **RetailFlavour** — a flavor on the canonical core, the same way HealthFlavour is.

## Consequences

- Positive: one core to secure, certify, and localise; cross-domain workflows become possible;
  CyShop maintenance cost → zero; a proven pattern (CyMed) is generalised.
- Negative / trade-offs: a real migration with financial-data risk (R09) — mitigated by the
  `D.3` dry-run + data-quality gates + read-only source retention.
- Follow-up: `D.3` migration M0–M5; deprecate CyShop JWT (ADR-0006); remove CyShop deploy
  pipelines; delete the `Cybercom-launch` scaffold.
- Revisit if: migration reconciliation surfaces CyShop data the canonical model genuinely
  cannot represent (then CDAC extends the model, not forks it).
