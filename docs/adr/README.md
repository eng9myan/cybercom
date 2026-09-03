# Architecture Decision Records

ADRs capture significant, hard-to-reverse decisions: context, the decision, and consequences.
Owned by the Cross-Domain Architecture Council (CDAC — see `docs/blueprint/F_governance_security_compliance.md`).

## Process

1. Anyone opens an ADR as a PR using `TEMPLATE.md`, status `Proposed`.
2. CDAC reviews at its weekly session (or async for non-blocking).
3. On acceptance: status → `Accepted`, merged, numbered.
4. Superseding: new ADR references the old; old status → `Superseded by ADR-NNNN`.
5. ADRs are immutable once accepted — change by superseding, not editing.

## Index

| ADR | Title | Status | Source |
|---|---|---|---|
| [0001](0001-canonical-core-is-cycom-platform.md) | Canonical core = CyCom + `platform/`; CyShop migrates in and is archived | Accepted | blueprint J.1 A3 |
| [0002](0002-modular-monolith-with-carve-outs.md) | Modular monolith with selective service carve-outs, not microservices-first | Accepted | J.1 A4 |
| [0003](0003-flavor-is-config-not-fork.md) | A vertical flavor is config + a thin pack, never a code fork | Accepted | J.1 A5 |
| 0004 | Tech stack: Django + DRF, Next.js, React Native, PostgreSQL, Redis, OpenSearch, Kafka/Redpanda | Proposed | J.1 A1 |
| 0005 | Cloud: AWS Gulf regions; KSA workloads on a sovereign region | Proposed | J.1 A2 |
| 0006 | Identity: Keycloak / CyIdentity is the single OIDC issuer; CyShop JWT deprecated | Proposed | J.1 A8 |
| 0007 | One canonical data model; flavor fields via registered `attributes` profiles or reviewed extension tables | Proposed | J.1 A5, C.0 |
| 0008 | Events are the integration backbone; transactional outbox → broker; no cross-domain table access | Proposed | C.0 |
| 0009 | API-first; URL-major versioning; two majors concurrent; 6-month deprecation window | Proposed | C.4 |
| 0010 | E-invoicing: one pluggable clearance engine, modes `SA_ZATCA` / `JO_JOFOTARA` / `AE_PEPPOL` | Proposed | J.1 A9 |
| 0011 | Payments: local PSPs primary + Stripe international; card data never on our servers (PCI SAQ-A) | Proposed | J.1 A7 |
| 0012 | Tenant isolation is defence-in-depth: queryset scoping + Postgres RLS + per-tenant DEK + object prefix | Proposed | C.5, F.2 |
| 0013 | DB migrations use expand/contract; never a breaking migration in the same deploy as dependent code | Proposed | C.6 |
| 0014 | Hosting platform (Odoo.sh-equivalent) is Phase 4, after first reference customers | Proposed | J.1 A13 |

ADRs 0004–0014: decision text is pre-stated from the blueprint; CDAC to ratify or amend in Phase 0.
