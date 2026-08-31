# MARKET_READINESS.md — Phase 0 Recommendation (2026-08-25)

> The buildout prompt's Phase 0 checkpoint. Answers: which product reaches a paying
> customer fastest, and how to sequence the rest. Grounded in the verified inventory
> (`SYSTEM_INVENTORY.md`), not feature-count.

## TL;DR

**Launch CyCom first — as a Commerce/Retail ERP.** Fold CyShop into it as the Commerce
vertical (already underway) rather than launching CyShop separately. CyMed is the
fast-follow #2 (bigger value, heavier compliance + longer sales cycle). This reorders the
prompt's 3-way race into a **2-track** plan.

## 1. % of a commercially-usable MVP that actually exists (functional + tested)

| Product | Est. MVP % | Basis |
|---|---|---|
| **CyCom** | **~70%** | 39 apps; core flows (catalog, POS+KDS, sales/quotations, inventory, accounting w/ real journals, provisioning wizard) built, unit-tested, and several **live-verified in-browser** this session. Self-serve signup wired. |
| **CyShop** | n/a (merging) | ~90% duplicate of CyCom; unique parts already harvested into CyCom. Not scored as a standalone launch. |
| **CyMed** | ~40–55% (unverified) | 16 healthcare apps on shared platform, structurally rich (FHIR, RCM, pharmacy, labs, portals). Not runtime-verified this session; healthcare needs clinical validation + compliance the others don't. |

## 2. What genuinely blocks a paying customer TODAY (vs "not Odoo-complete")

**Real blockers (CyCom):**
1. **Payment collection** — no gateway. `register` only raises a bank-transfer-pending invoice. Blocks self-serve paid conversion. (Manual invoicing is a viable interim for a first hand-held customer.)
2. **Signup completion needs Keycloak** — the public signup flow 500s without the Docker/Keycloak stack (realm provisioning). Fine for demos via dev-auth; blocks true self-serve until Keycloak is stood up on a real box.
3. **No hosting/provisioning platform** — no git-branch env / one-click tenant instance delivery yet (prompt's Section 8). A first customer can be hosted manually; scaling needs this.

**Not blockers (don't over-invest pre-launch):** full Odoo parity (MRP depth, Studio, every accounting report), RTL polish, the two non-launch verticals.

**CyMed additional blockers:** clinical data validation, HIPAA/compliance posture, and a much longer B2B healthcare sales cycle — structural, not quick fixes.

## 3. Ranking by fastest path to first paying customer

1. **CyCom (Commerce/Retail)** — most built, demo-ready NOW (seeded café demo + KDS verified live), self-serve signup wired, absorbing CyShop's commerce value. Shortest gap to revenue.
2. **CyMed** — highest ceiling (hospitals, e-gov healthcare) but longest runway: compliance, clinical validation, enterprise sales. Build in parallel at lower allocation; launch second.
3. **CyShop standalone** — **do not launch.** Merge into CyCom; archive.

## 4. Recommendation

- **Go-to-market push: CyCom**, positioned first at Retail/F&B/Commerce (the vertical with working, visual, differentiated flows — POS + live KDS). Broaden to general ERP messaging after the first reference customer.
- **CyShop**: finish folding into CyCom as the Commerce industry template (catalog ✓, POS/KDS ✓, sales ✓, onboarding ✓ done; remaining: Commerce dept-pack in provisioning, archive repo).
- **CyMed**: continue in parallel, lower agent allocation; its own market-readiness audit is the next Phase-0-style pass before it gets a launch date.

## Path-to-revenue backlog for CyCom (what Phase 1+ should attack, in order)

1. **Hosted demo box** (near-done this session) — reference environment for sales. Cheapest revenue enabler.
2. **Payment gateway** — Stripe/regional (HyperPay/PayTabs for JO/SA/AE) on the `register` flow.
3. **Keycloak on a real box** — unblocks true self-serve signup end-to-end.
4. **Commerce provisioning dept-pack** — so "Retail" is a one-click industry template.
5. **Tenant hosting/provisioning platform** (prompt Section 8) — for scaling beyond hand-held customers.

## Checkpoint

Per the prompt's own gate: **stopping here for your review before any Phase 1 backlog build.**
Open decisions that change execution are listed in the chat report accompanying this doc.
