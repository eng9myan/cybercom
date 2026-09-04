# LAUNCH READINESS — CyShop (commerce), 2026-09-04

> Goal (founder): launch the shop product + website now, start bringing clients,
> build the rest of the ecosystem incrementally without delaying launch.
> This is the honest state and the exact path.

---

## 1. What "CyShop" is at launch

**CyShop = the customer-facing brand for CyberCom's commerce offering.**
It is delivered by the **CyCom commerce engine** (`cycom/` backend + `cycom/cycom-erp` Next.js
frontend) — *not* the standalone `cyshop/` repo, which is ~90% duplicate and is being archived
(ADR-0001). Everything a launch client needs is in CyCom; nothing they build now has to be
thrown away when the flavor engine lands (it becomes RetailFlavour).

**In scope for launch:** catalog, POS + live KDS, inventory (multi-branch, costing),
accounting with real journal posting, self-serve signup, subscription tiers, the 10-step
provisioning wizard + AI-propose, the marketing/subscription **website**.

**Deferred (built after launch, behind flags — do not block on these):** the other ~50
flavors, CyMed, CyMart marketplace, Flavor Studio, the hosting platform, full Arabic i18n,
ZATCA/JoFotara live clearance (needed only for KSA/JO *tax invoices* — see §4).

---

## 2. Verified working today (local, 2026-09-04)

| Check | Result |
|---|---|
| `cycom` backend — `manage.py check` | clean, 0 issues |
| migrations | in sync, apply clean (SQLite + Postgres paths) |
| `pytest` (backend) | 103/103 pass (coverage thin — §5) |
| commerce demo seed (`seed_demo_commerce`) | populates a tenant: 20 catalog products, 28 inventory products, 9 POS orders, 5 KDS tickets, 4 receipts, quotations |
| `GET /api/v1/catalog/products/` (dev-auth) | **200**, real data |
| `GET /api/v1/pos/orders/` | **200**, real data |
| `cycom-erp` frontend — `npm run build` (Next 16) | **clean**; routes incl. `/signup`, `/subscriptions`, `/setup`, `/setup/warehouse`, `/pos`, `/kds` |
| `cycom-erp` — `npm test` | 6/6 pass |
| `website` — `npm run build` (Turbo monorepo) | **clean** |
| signup + payment-seam tests | 7/7 pass |
| **Fixed this session** | `/api/schema/` 500 (audit serializer `read_only_fields`) → now generates |

**The signup → pay → provision → POS loop was proven end-to-end against the real stack
(real Keycloak realm, payment-simulate, tenant flips active) in the 2026-08-31 session**
(`PROJECT_STATE.md`). This session re-confirmed every piece builds and the commerce API serves.

**Conclusion: the launch product is code-complete for a soft launch.** The remaining work
is deployment + one payment gateway + (for KSA/JO) e-invoicing — all listed below.

---

## 3. Two launch tiers

### Tier 1 — Soft launch (start bringing clients in ~days)

**Model:** hand-provisioned tenants, manual bank-transfer invoicing, high-touch onboarding.
JO first (home turf, bilingual-tolerant buyers, no e-invoicing mandate blocking).

**Needs (yours):**
- A Linux VM with Docker + 2 DNS records (`app.`, `auth.`) + a TLS reverse proxy.
  The repo has one-command tooling for this: `infrastructure/scripts/deploy_box.sh` (full
  stack) or `deploy_micro.sh` (free-tier native). See `GO_LIVE.md`.
- Secrets you set (never shared): `DJANGO_SECRET_KEY`, DB passwords, Keycloak admin + client secret.
- Decide billing: **manual invoice** (no gateway needed) is fine for the first clients.

**Then:** run `GO_LIVE.md` → verify the checklist → hand-provision client #1 via `/setup`
(Commerce template) → they run real POS + KDS + inventory + books → bill by invoice →
mark paid → tenant active. Capture a reference + case study.

**What CyberCom does for Tier 1:** the deploy is scripted; onboarding is the wizard.
No new code required.

### Tier 2 — Self-serve GA (weeks after Tier 1)

Adds: one **live payment gateway** (HyperPay recommended — JO+SA+UAE coverage) wired to the
existing seam; **Keycloak on the box** confirmed for end-to-end signup; signup→pay→provision
running unattended. For KSA/JO clients issuing tax invoices: **e-invoicing clearance**
(`SA_ZATCA` / `JO_JOFOTARA`) — the biggest remaining build (`L.3`), ~2–3 weeks, can run in
parallel with Tier-1 selling since JO's mandate is still rolling out and KSA clients can
start on internal invoices while it lands.

---

## 4. Mine vs yours

| Task | Owner | Status |
|---|---|---|
| Backend/frontend/website build clean | CyberCom | ✅ done |
| Commerce demo tenant for sales | CyberCom | ✅ done (`seed_demo_commerce`) |
| `/api/schema/` + Swagger + dev portal schema | CyberCom | ✅ fixed this session |
| Deploy scripts (single-box, OCI, compose) | CyberCom | ✅ in repo (`infrastructure/`) |
| Raise backend test coverage on money paths | CyberCom | ✅ **done** — GL-balance/atomicity, POS checkout GL+stock+oversell, sales quotations, e-invoicing (cycom 103→158, cymed 486/23/6→515/0) |
| Wire a real PSP to the payment seam | CyberCom | ✅ **HyperPay done** (`platform/tenant/payments.py`): create_checkout + verify (redirect-return) + encrypted webhook (fail-closed). Enabled by 3 env vars + `CYCOM_PAYMENT_PROVIDER=hyperpay`. PayTabs/Moyasar = same pattern when needed. |
| **JoFotara clearance engine** | CyberCom | 🟢 **engine + XAdES-B signing + wiring + tests** (`platform/einvoicing/`, migration 0004). Remaining = XSD/Schematron + ISTD sandbox onboarding (regulator cycle). |
| **ZATCA clearance engine** | CyberCom | 🟢 **`sa_zatca` built** — UBL, TLV QR, ECDSA stamp, clearance (B2B) / reporting (B2C), wired. Remaining = ZATCA CSID compliance onboarding + full UBLExtensions block. |
| Tenant-write isolation (the "forgot tenant_id" bug class) | CyberCom | ✅ **closed** — `TenantScopedMixin.save()` auto-fills from ambient context or raises clearly; `TenantContextMiddleware` wired (§2.2) |
| Arabic/RTL for POS + receipts | CyberCom | ⏳ workstream (`RTL_AUDIT.md`) — **not a JO soft-launch blocker** |
| **A host + DNS + TLS** | **You** | ⛔ blocks Tier 1 |
| **Secrets** (DB, Django, Keycloak) | **You** | ⛔ blocks Tier 1 |
| **HyperPay account + keys** (`HYPERPAY_ENTITY_ID` / `_ACCESS_TOKEN` / `_WEBHOOK_SECRET`) | **You** | ⛔ blocks Tier 2 self-serve card payments (code is ready) |
| **Confirm 2 payroll rates** (SA GOSI scheme, UAE national %) | **You** | ⛔ blocks payroll compliance claims |
| Pick KSA sovereign region (if selling KSA) | **You** | ⛔ blocks KSA data-residency |
| Business registration / merchant agreements / terms + DPA | **You** | ⛔ blocks paid contracts |

**The only hard blocker to starting Tier 1 is infrastructure you control.** The code is ready.

---

## 5. Known code gaps (not launch blockers, but on the list)

| Gap | Impact | Plan |
|---|---|---|
| Backend test coverage: **126 tests** (was 103); money paths now covered (GL balance, POS checkout GL + stock, sales, JoFotara) | remaining apps thinner | keep raising toward `H` Q1 before migrated data lands |
| `/api/schema/` generates but 104 non-fatal warnings (APIViews without serializers) | thin auto-docs on some endpoints | polish during dev-portal build |
| Gap-fill apps (discuss, fleet, helpdesk, leave, marketing, planning, plm, project, recruitment) — little/no test coverage | shipped but unproven | smoke tests before any are exposed in a GA flavor |
| No live PSP wired | manual invoicing only | Tier 2 |
| e-invoicing: JoFotara **engine built + tested**; XAdES signing + XSD validation + ISTD onboarding remain | JO tax invoices need the onboarding done; KSA needs `sa_zatca` too | Tier 2, `specs/einvoicing-clearance-engine.md` §6 |
| RTL/Arabic greenfield | SA/UAE credibility | funded workstream |
| ~~CyMed 5 nphies tests failing~~ | ~~CyMed~~ | **fixed** — `TenantScopedMixin.save()` auto-fill (§2.2 implemented). **CyMed suite 515/0.** |

---

## 6. The sequence — launch now, build the ecosystem behind it

```
NOW ──► Tier 1 soft launch
        • you: VM + DNS + TLS + secrets  (deploy_box.sh / GO_LIVE.md)
        • CyberCom: run go-live checklist, fix whatever the box surfaces
        • sell: 3 friendly JO F&B/retail clients, hand-provisioned, manual invoice
        • outcome: revenue + references, ZERO new code needed

+2–4 wk ─► Tier 2 self-serve  (parallel with selling)
        • CyberCom: wire 1 PSP · confirm Keycloak on box · signup→pay→provision unattended
        • CyberCom: start ZATCA + JoFotara clearance engine
        • you: PSP account, payroll rates, KSA region decision

+1–3 mo ─► Phase 1 canonical work  (does not touch the running launch product)
        • TenantScopedManager + tenant_context (closes the isolation-gap bug class)
        • canonical data-model v1 migrations (additive, M1)
        • flavor engine promotion → RetailFlavour is the launch product, formalised
        • CyShop-standalone data (if any live) migrates in; repo archived

+3–6 mo ─► Phase 2–3  (new revenue, launch product keeps running)
        • RetailFlavour GA · HealthFlavour (CyMed re-homed, 510/5 tests) · pilots
        • Flavor Studio · developer portal · CyMart marketplace
        • more flavors, per flavor-registry.yaml waves

+6–18 mo ─► the full ecosystem  (G phases 4–7)
        • hosting platform (zero-touch provisioning) · partner programme
        • wave-3 flavors · GCC expansion · localization-pack SDK
```

The launch product is **stable and independently deployable** (`README.md`). Everything after
Tier 1 is additive and flag-gated — no phase blocks the running business.

---

## 7. Immediate next actions

**You:**
1. Stand up a VM (2 vCPU / 4 GB is plenty for the first clients) + point `app.` and `auth.` DNS at it.
2. Run `infrastructure/scripts/deploy_box.sh` per `GO_LIVE.md`, setting your secrets.
3. Tell me it's up — I run the go-live verification checklist against it and fix anything.
4. Pick the first PSP (HyperPay recommended) and open the account.
5. Confirm the 2 payroll rates.

**CyberCom (me), starting now, in order:**
1. Raise backend coverage on the money paths (POS, sales, accounting, payroll, signup/payment).
2. Wire the payment-seam to a real PSP (stub-testable now, live when you have keys).
3. Build the e-invoicing clearance engine (`SA_ZATCA` + `JO_JOFOTARA`).
4. Then Phase-1 canonical work.
