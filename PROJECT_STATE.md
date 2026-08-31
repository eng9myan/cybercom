# PROJECT_STATE.md — CyberCom ERP Buildout

Delivery-lead log. Model tier per task + phase status. Short by design; detail lives in the named docs.

## Decisions locked
- **Launch product: CyCom** (Commerce/Retail-first). CyShop folds in as a vertical (merge underway). CyMed = fast-follow #2. — approved 2026-08-25.
- **Orchestration: ruflo** (claude-flow) — installed (`ruflo-core`/`swarm`/`agentdb`), `npx ruflo init` run, daemon up. MCP memory layer connects on next real-terminal restart; not blocking.

## Phase status
| Phase | State | Deliverable | Model tier |
|---|---|---|---|
| 0 — Market readiness | ✅ done | `SYSTEM_INVENTORY.md`, `MARKET_READINESS.md` | Opus (judgment call) |
| 1 — Gap analysis (CyCom) | ✅ done | `GAP_ANALYSIS.md` | Opus (analysis) |
| 2 — Build execution | 🔨 in progress | P0/P1 backlog, one by one | Opus/Sonnet |

### Phase 2 progress (build all, one by one)
| # | Item | Prio | State | Notes |
|---|---|---|---|---|
| 1 | Payment gateway | P0 | ✅ done | Backend seam+endpoints already existed (prior session); added frontend checkout render in /signup + 5 tests. Live click-through still gated by Keycloak (item 2). |
| 2 | Keycloak on a real box | P0 | ✅ built | Prod compose + .env template + realm reuse + README-prod runbook. Compose validated. Deploy+verify = user's infra. |
| 3 | Hosting/provisioning platform | P1 | ⏸ deferred | prompt §8 — needs cloud target; user chose to skip to verifiable app-code first. |
| 4 | Accounting reports + multi-currency | P1 | ✅ done | Reports already existed+routed+tested; added base-currency conversion via exchange_rate + 2 tests (14 pass). |
| 5 | CRM pipeline | P1 | ✅ done | Added Activity model + pipeline funnel endpoint (count/value/weighted) + activities API; migration 0003 + 3 tests. |
| 6 | RTL/Arabic | P1 | 🟡 audit+foundation | Was greenfield. Added LocaleDirection (dir/lang) + layout wiring + RTL_AUDIT.md roadmap. Full i18n = own workstream. |
| 7 | Payroll beyond JO | P1 | ✅ done | Added SA GOSI (Saudi 2026 10.75/12.75 + legacy + expat 2%, SAR 45k cap) + UAE gratuity (21/30-day, 24mo cap) + GPSSA national + country dispatcher. 11 tests. Rates web-sourced+cited; 2 flagged for your confirmation (SA scheme choice, UAE national 5/12.5 vs 11/15). |

**Verifiable-here backlog complete.** 42 tests green across all items built this session.

### FULL-STACK LOCAL TEST (2026-08-31) — signup→pay→activate proven end-to-end
Brought up the real stack locally: Docker (daemon started), docker-compose.cycom-dev.yml (Postgres cycom_new + Redis + Keycloak 26 with realm auto-import, remapped to :8085 via dev-kc8085.override.yml because :8080 was held by AgentService). Backend on host :8092 via core.settings (real auth, dev-auth OFF), fake payment provider. Migrated Postgres, seed_packs, bootstrap_platform_realm (created Django IdentityRealm + KC platform-admin + client secret).
- **register 201** → real tenant + real Keycloak realm/user + invoice + checkout. **pay (simulate) → tenant ACTIVE, invoice PAID** (confirmed in Postgres). The loop that was blocked all session now works.
- **2 PRODUCTION BUGS FIXED** (dev-auth had masked them): (a) shared/auth/auth_middleware.py CyIdentityAuthMiddleware 401'd public signup/payment paths → added allowlist; (b) cycom/core/middleware/tenant.py TenantIsolationMiddleware 400'd them ("X-Tenant-ID missing") → exempt public paths (tenant_id=None). Protected endpoints still 401 without token (exemptions correctly scoped).
- Follow-up chip spawned: apply the tenant-middleware fix to cymed/cyvault/cyed (per-product copies).

Remaining: item 3 hosting platform (cloud target), full Arabic i18n, confirm the 2 payroll rates, then upload to servers/domain (GO_LIVE.md).
| 3 — Hosting platform | ⬜ not started | Odoo.sh-equivalent | — |
| 4 — Business build-out | ⬜ not started | `BUSINESS_PLAN.md` | Sonnet/Fable (prose) |

## Corrections to the buildout prompt (for the record)
- Stack is **Django + DRF + Next.js**, not Laravel/Inertia. Any launch scaffold must match.
- CyShop is **not** a 3rd launch candidate — ~90% duplicate; merging into CyCom.
- claude-flow zip/`npm link`/parallel `cybercom-workspace` steps skipped — used the npm/plugin install in place at `D:\cybercom`.

## Open decision (blocks Phase 2 start)
Which path for the two P0 enablers — build now (Keycloak-on-a-box + payment gateway) vs hand-provision the first customer and defer both to fast-follow. See chat.
