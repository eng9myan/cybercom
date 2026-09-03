# BUSINESS_PLAN.md — CyCom Launch Business Plan

> Internal launch plan for **CyCom**, CyberCom's multi-tenant ERP (an Odoo-equivalent).
> Pragmatic and honest, not investor hype. Grounded in the verified engineering docs:
> `SYSTEM_INVENTORY.md`, `MARKET_READINESS.md`, `GAP_ANALYSIS.md`, `PROJECT_STATE.md`,
> `GO_LIVE.md`. Where hard financials belong, this doc gives a **framework and stated
> assumptions** for the founder to fill — it does **not** invent revenue, customer counts,
> or funding.
>
> Author: CyberCom (business build-out). Date: 2026-08-31. Status: draft for founder review.

---

## 1. Executive summary

**CyCom is a multi-tenant, self-serve ERP built on Django + DRF + Next.js.** It is functionally an Odoo-equivalent — sell, stock, buy, book, pay staff — but its **strongest, most-tested, most-differentiated surface is Commerce/Retail**, specifically **POS + a live Kitchen Display System (KDS)** for food & beverage and retail. That is where we launch.

**Positioning at launch: CyCom is a Commerce/Retail ERP** (POS + KDS + inventory + accounting, self-serve), not "a general ERP." We earn the right to the broader "run your whole business" message *after* the first reference customer. This is deliberate: the general-ERP claim is credible on paper (39 apps) but only the Commerce surface is verified end-to-end today.

**Product family and sequencing:**
- **CyCom (Commerce-first)** — launch now. CyShop, a near-duplicate standalone build, **folds into CyCom** as the Commerce vertical; its unique value (catalog, POS Device/receipt/KDS, quotations, onboarding UX) is already harvested. CyShop does **not** launch separately and its repo is archived.
- **CyMed (healthcare)** — fast-follow #2. Higher ceiling (hospitals, e-gov health), but longer runway: clinical validation, compliance, enterprise sales cycle. Built in parallel at lower allocation; earns its own launch date after a dedicated readiness pass.

**Target markets:** Jordan, Saudi Arabia, UAE SMBs — F&B and retail first. Payroll is localized for **JO, SA (GOSI), and UAE (gratuity/GPSSA)**. Arabic/RTL support has a foundation and an audit roadmap, but full bilingual polish is still in progress.

**The honest gap to first revenue is not features.** The operational core is present and tested. What stands between us and a scalable paid launch is a short list of **enablers**: a production payment gateway wired live, Keycloak stood up on a real host, and — for scaling beyond hand-provisioned customers — an **Odoo.sh-equivalent hosting platform that is not yet built** (it is a roadmap item). The full-stack signup → pay → activate loop has already been **proven end-to-end locally** against the real stack (real Keycloak realm, real payment simulate, tenant flips active), which de-risks the launch considerably.

**The plan in one line:** land the first paying Commerce customer by **hand-provisioning** them (manual invoicing or a single gateway), turn that into a reference, then invest the proceeds/learnings into self-serve + the hosting platform, with CyMed following behind.

---

## 2. Product & positioning

### 2.1 What CyCom is

A subscription, multi-tenant ERP delivered as a hosted web app:
- **Backend:** Django + Django REST Framework on a shared `platform/` core (identity, tenant, provisioning, audit, events, notifications, AI). PostgreSQL in production.
- **Frontend:** Next.js 16 (App Router, TypeScript) — the CyCom ERP UI.
- **Auth:** real OIDC/Keycloak in production; a dev-auth shim for demos/local only.
- **Onboarding:** a 10-step provisioning wizard with **industry templates, department packs, country packs, and an AI-propose step** that suggests a module set from a business description.
- **Billing:** self-serve signup that raises a subscription invoice; manual bank transfer is live today, with Stripe/HyperPay/PayTabs pluggable behind a payment seam.

### 2.2 The launch wedge: Commerce/Retail F&B

CyCom's Commerce surface is the part that is **built, tested, and live-verified**: product catalog (variants/kits/categories), **POS** (sessions, orders, payments, layaway, discount approval, journal posting), **live KDS** (kitchen tickets update in real time), receipts, and a Commerce quick-setup onboarding path. A seeded café demo (catalog + POS + live KDS + quotations) exists for sales.

**Why lead with F&B/retail and not "general ERP":**
- It is the surface where our flows are **visual, differentiated, and demonstrable in minutes** (ring a sale, watch the ticket hit the kitchen screen).
- SMB F&B/retail buyers have an **urgent, concrete pain** (POS + kitchen ops + stock + basic books) and a **short sales cycle** — the opposite of enterprise ERP.
- It lets us make a **narrow, true claim** we can prove, rather than a broad claim we'd have to defend across 39 apps.

### 2.3 Positioning vs Odoo

Odoo is the reference point — a broad, modular, open-core ERP with a large app catalog and a per-app / per-user commercial model, plus Odoo.sh hosting. We do **not** out-breadth Odoo at launch, and we shouldn't try.

| Dimension | Odoo | CyCom (launch reality) |
|---|---|---|
| Breadth | Very broad, mature across every module | Broad on paper (39 apps); **verified** on the Commerce core |
| Commerce/F&B | POS module exists; KDS is add-on/uneven | **POS + live KDS as a first-class, tested differentiator** |
| Localization | Global, community-driven regional packs | **Purpose-built for JO/SA/UAE**: payroll GOSI/gratuity/GPSSA, Arabic/RTL on the roadmap |
| Onboarding | Configuration-heavy; partner-led | **AI-propose + industry templates**: describe the business, get a module set |
| Hosting | Odoo.sh (mature) | **Not built yet** — hand-hosted first, platform on roadmap |
| Buyer motion | Partner/reseller ecosystem, self-serve online | Self-serve signup wired; **hand-held first customer**, then self-serve |

**Honest read:** Odoo wins on breadth, maturity, ecosystem, and hosting today. CyCom wins — for a specific buyer — on **regional fit (Arabic + local payroll/tax trajectory), F&B/retail demonstrability (KDS), and guided AI onboarding**. Our job at launch is to win that specific buyer, not to beat Odoo on a feature matrix.

### 2.4 Positioning vs regional ERP players

The regional field (local ERP vendors, on-prem accounting suites, and regional Odoo partners across JO/SA/UAE) generally competes on local compliance and implementation services, often with heavy on-prem/customization models and long deployment cycles. CyCom's counter-positioning:
- **Cloud-native, self-serve, subscription** — days to value, not months of implementation.
- **Regional localization built in** (payroll, and Arabic/tax on the roadmap) rather than bolted on.
- **Modern UX** (Next.js) and **AI-guided setup** vs. dated on-prem interfaces.

We should be candid internally: many regional buyers value the **local partner relationship and hand-holding**. Our early motion (hand-provisioned first customers, high-touch onboarding) actually leans into that expectation rather than fighting it.

---

## 3. Target market & ICP

### 3.1 Ideal Customer Profile (launch)

- **Geography:** Jordan first (home turf, easiest to support and reference), then Saudi Arabia and UAE.
- **Segment:** SMBs in **F&B (cafés, restaurants, cloud kitchens, small chains) and retail** (single-store to small multi-branch).
- **Size:** roughly 1–20 locations, 5–100 staff — big enough to pay for software and feel ERP pain, small enough to buy without a 6-month procurement cycle.
- **Trigger:** opening/expanding, outgrowing a basic POS or spreadsheets, or needing local payroll + books alongside POS.
- **Buyer:** owner-operator or ops/finance lead — a single decision-maker, not a committee.
- **Why they pick us:** POS + live kitchen display that works, inventory + accounting behind it, local payroll, and a setup they can actually complete.

**Explicitly not the launch ICP:** large enterprises, regulated healthcare (that's CyMed), manufacturing-heavy businesses needing MRP depth, and pure-eCommerce sellers needing an online storefront (P2 on our roadmap).

### 3.2 TAM / SAM / SOM (qualitative — assumptions the founder validates)

We deliberately avoid fabricated numbers. Instead, here is the **reasoning framework and the assumptions to fill**:

- **TAM (total addressable):** all SMBs across JO/SA/UAE that could run a cloud ERP. Directionally large and dominated by SA (biggest economy) and UAE (highest digitization/spend), with JO smaller but our beachhead. *Founder to size using national SMB registries / statistics authorities per country.*
- **SAM (serviceable available):** the slice we can actually serve at launch — **F&B + retail SMBs in JO/SA/UAE** that (a) want cloud/subscription software, (b) are served by our current localization (JO/SA/UAE payroll), and (c) don't need capabilities we lack (online storefront, MRP, healthcare). *Assumption to validate: what fraction of regional SMBs are F&B/retail, and what fraction are ready to move off legacy POS/on-prem.*
- **SOM (serviceable obtainable, ~24 months):** what one small team can realistically win given a hand-provisioned-then-self-serve motion, no hosting platform at launch, and Arabic still maturing. This is **a function of sales capacity and onboarding throughput**, not market size — early on we are capacity-bound, not demand-bound.

**Bottom-up unit framework (fill in):**
```
SOM (annual recurring revenue) ≈
    (# customers we can land & onboard per quarter)
  × (4 quarters, compounding, minus churn)
  × (average revenue per account, from §4 pricing)
  × (net retention)
```
The honest early constraint is the **left-most term** — landing and onboarding throughput while everything is high-touch. Do not model hockey-stick growth before the self-serve + hosting platform exists (§6).

---

## 4. Pricing & packaging

### 4.1 Tiers (already coded)

CyCom already ships three subscription tiers — **Starter / Professional / Enterprise**. Packaging principle: gate on **modules + usage (locations/users/POS terminals) + support level**, not on hiding core functionality.

| Tier | Who it's for | Includes (indicative) | Gated on |
|---|---|---|---|
| **Starter** | Single-location café/shop | Commerce core: catalog, POS, KDS, basic inventory, basic books | 1 location, small user/terminal cap, community/email support |
| **Professional** | Small multi-branch / growing | + multi-location, payroll (local), full accounting reports, CRM pipeline, priority support | more locations/users/terminals |
| **Enterprise** | Small chains / higher needs | + advanced provisioning, SSO, higher limits, onboarding assistance, SLA | high/negotiated limits, dedicated support |

*The founder sets the actual price points.* Anchoring guidance below.

### 4.2 Anchoring to Odoo (conceptual, no fabricated competitor prices)

Odoo's public commercial model is conceptually **per-app and/or per-user, billed as a subscription, with a hosted option (Odoo.sh) on top**. We do **not** quote Odoo's exact figures here (they change and vary by region/promotion — the founder should pull current published pricing directly).

Use Odoo's *structure* as the anchor, and differentiate on *shape*:
- **Prefer per-location / per-terminal pricing over pure per-user for the F&B/retail ICP** — it maps to how these businesses think (a café pays per till, not per employee who might touch the POS). This is a cleaner story than Odoo's per-user model for our wedge.
- **Bundle the Commerce core** (POS + KDS + inventory + basic books) into every tier so the buyer isn't nickel-and-dimed on the thing they came for; charge up-tier for **scale (locations/users), payroll, advanced modules, and support**.
- **Undercut or match on entry price, win on regional fit + onboarding**, not on being the cheapest.

### 4.3 Hosted vs self-managed

- **Hosted (primary, launch):** we run it. Simplest for the SMB ICP; it's the whole point of self-serve subscription. At launch this is **hand-operated hosting** (see §6) — priced into the subscription.
- **Self-managed (later / Enterprise-only):** the stack is Dockerized (`GO_LIVE.md`), so a technical customer *could* self-host. Treat this as an **Enterprise/partner option, not a launch SKU** — it adds support surface we can't afford to spread thin early.

### 4.4 Per-module thinking

The provisioning engine already models modules as packs, so **per-module add-ons are technically natural** (e.g., add Payroll, add advanced Accounting, later add Manufacturing/Project). Recommendation: **keep the launch pricing simple** (three tiers with the Commerce core bundled), and introduce **module add-ons only once buyers ask** — avoid a confusing à-la-carte matrix at launch when the story needs to be crisp.

### 4.5 Billing mechanics

- **Live now:** manual bank transfer — signup raises a subscription invoice; finance confirms; tenant activates. Fine for the first hand-held customers.
- **Pluggable:** Stripe (international cards) + **HyperPay / PayTabs** (regional gateways for JO/SA/UAE) behind the existing payment seam. Wiring one live gateway is a P0 for self-serve conversion (§7).

---

## 5. Go-to-market sequencing

The GTM mirrors the engineering reality: **prove it hand-held, then automate.**

### Stage 0 — Reference environment (done / near-done)
A hosted demo tenant (seeded café: catalog + POS + live KDS + quotations) exists for sales. This is the cheapest revenue enabler — a sales rep can show the KDS lighting up in minutes.

### Stage 1 — Land the first paying Commerce customer (hand-provisioned)
- Target a **friendly JO F&B/retail SMB** where we can be high-touch.
- **Hand-provision** their tenant on our host; onboard them personally via `/setup` (Commerce template).
- **Bill via manual invoice** (bank transfer) or a single live gateway — do **not** wait on full self-serve.
- Goal: a **live, happy reference customer** running real POS + KDS + books, plus a case study and testimonial. This de-risks everything downstream and funds/justifies the next stage.

### Stage 2 — Turn on self-serve
- Stand up **Keycloak on a real box** (unblocks end-to-end signup/login) and **wire one live payment gateway** (regional first: HyperPay or PayTabs).
- Open **self-serve signup → pay → auto-provision** for the Commerce template. (The full loop is already proven locally against the real stack — this is deployment + a gateway, not new invention.)
- Tighten onboarding so a buyer can go from signup to ringing a sale **without us in the room**.

### Stage 3 — Scale delivery (hosting platform)
- Build the **Odoo.sh-equivalent hosting platform** (§6) so tenants are provisioned and operated **without manual ops per customer**. This is the gate to scaling past a handful of hand-held accounts.

### Stage 4 — CyMed fast-follow
- Once CyCom Commerce is self-serving and referenceable, give **CyMed its own readiness pass** (clinical validation, compliance posture) and launch it as vertical #2 on the same shared platform.

**Broadening the message:** only after Stage 1's reference do we expand outward from "Commerce/Retail ERP" toward "run your whole business" — and even then, lead with the verified surface and add modules as proof accumulates.

---

## 6. The hosting platform (commercial delivery mechanism) — roadmap, not built

**What it is:** the Odoo.sh-equivalent — a platform that turns "a new paying tenant" into an automated, operated instance: one-click/API tenant provisioning, environment management (ideally git-branch-style staging/prod per tenant), upgrades, backups, and monitoring, without an engineer doing manual ops per customer.

**Current reality (be honest):** **it is not built.** What exists today is the **in-app provisioning engine** (industry templates + dept/country packs + blueprint→provision + AI-propose) and Dockerized deployment assets (`GO_LIVE.md`). That is enough to **hand-provision** customers one at a time — it is **not** a self-operating hosting product.

**Why it matters commercially:** it is the mechanism that makes the **subscription model scale**. Without it, every new customer costs us manual ops time, capping growth (this is the §3.2 SOM constraint). With it, self-serve signup can flow straight into a running, isolated, upgradable instance.

**Sequencing:** deliberately **after** the first reference customer and self-serve enablers. Building the hosting platform before we have a paying customer would be premature optimization. It is a **P1 roadmap item** (§7), gated behind proving demand.

---

## 7. Roadmap (tied to the GAP_ANALYSIS backlog)

Priorities use the GAP_ANALYSIS convention: **P0** blocks a first paying self-serve customer · **P1** needed for credible commercial launch · **P2** parity polish after launch.

### P0 — enablers for a paying customer
| Item | Status | Notes |
|---|---|---|
| **Payment gateway** | Backend seam + endpoints built; frontend checkout added | Wire **one live gateway** (HyperPay/PayTabs regional, or Stripe) for real card capture. Manual invoicing covers the first hand-held deal. |
| **Keycloak on a real box** | Prod compose + runbook built; **loop proven locally** | Deploy on the production host to unblock true self-serve signup/login. (Hand-provisioned customers can launch before this.) |

*Both P0s are effectively "deploy + configure," not greenfield — the signup→pay→activate loop already ran end-to-end against the real stack locally, fixing two production auth/tenant middleware bugs in the process.*

### P1 — for a credible commercial CyCom
| Item | Status | Notes |
|---|---|---|
| **Hosting/provisioning platform** | Not built (deferred) | §6 — the scaling mechanism. Biggest net-new build. |
| **RTL/Arabic i18n** | Audit + foundation done (`RTL_AUDIT.md`) | LocaleDirection + layout wiring in; **full bilingual is its own workstream**. Hard requirement for SA/UAE credibility. |
| **Accounting reports + multi-currency** | Done (reports routed/tested; base-currency conversion added) | Keep polishing (tax returns, bank recon) as buyers demand. |
| **CRM pipeline** | Done (Activity model + funnel endpoint) | UI polish remains. |
| **Payroll beyond JO** | Done (SA GOSI, UAE gratuity/GPSSA) | **Two rates flagged for founder confirmation** (SA scheme choice; UAE national %). Confirm before quoting compliance. |

### P2 — after first launch
eCommerce storefront (omnichannel), loyalty/promotions, MRP depth, Project depth, Studio-style end-user field/form designer, multi-company within a tenant.

---

## 8. Risks & mitigations (honest)

| Risk | Why it's real | Mitigation |
|---|---|---|
| **Hosting platform not built** | Every customer needs manual ops; caps scale (the SOM constraint). | Hand-provision the first few (Stage 1); prioritize the platform as the top P1 build *after* proving demand. Don't promise self-service scale we can't yet operate. |
| **Full Arabic/RTL i18n pending** | JO/SA/UAE buyers expect Arabic; only foundation + audit exist. | Lead in JO (bilingual-tolerant, English-comfortable buyers) first; treat RTL as a funded workstream before pushing hard into SA/UAE; be honest with early customers about status. |
| **Live payment gateway not yet wired** | Blocks self-serve paid conversion. | Manual invoicing for hand-held customers now; wire one regional gateway before opening self-serve. Seam already exists — low technical risk. |
| **General-ERP claim outruns verified surface** | Only Commerce is end-to-end verified; 39 apps are uneven. | **Position as Commerce ERP at launch**; broaden only after the reference customer. Don't sell modules we haven't run. |
| **CyMed compliance/clinical validation** | Healthcare needs HIPAA-class posture + clinical validation + long sales cycle. | Keep CyMed as fast-follow with its **own** readiness pass; do not let it distract launch focus or borrow CyCom's "verified" credibility. |
| **Single-founder / small-team capacity** | High-touch onboarding + no hosting automation = throughput bound. | Sequence deliberately (land one, then automate); resist scaling sales before self-serve + hosting exist; price to value (fewer, better accounts) early. |
| **Competing with Odoo's breadth & ecosystem** | Odoo is mature, broad, well-hosted, partner-backed. | Don't fight on breadth. Win the **specific F&B/retail regional buyer** on KDS demonstrability, local payroll/tax, Arabic trajectory, and AI-guided onboarding. |
| **Test coverage uneven outside the built surface** | Strong on catalog/POS/sales; thinner elsewhere. | Only launch/sell the well-tested surface; add coverage as modules enter the sold set. |
| **Payroll rate correctness** | Compliance mis-statement is a trust/legal risk. | **Confirm the two flagged rates** (SA scheme, UAE national %) before making compliance claims; cite sources. |
| **Key-person / infra secrets** | Prod needs a host, DNS, TLS, secrets the founder controls. | `GO_LIVE.md` is the exact runbook; secrets stay with the founder; document ops so it isn't one person's head. |

---

## 9. 90-day launch plan

Concrete milestones. Dates are day-offsets from kickoff; the founder anchors to a real start date. "Owner" left generic for a small team to assign.

### Days 0–30 — Production up + first customer in pipeline
- [ ] Provision the **production host** (Linux VM + Docker), DNS (`app.`, `auth.`), TLS reverse proxy — per `GO_LIVE.md`.
- [ ] Deploy **Keycloak (prod)** and the **backend + workers + frontend**; run migrate / seed_packs / bootstrap_platform_realm.
- [ ] Run the **go-live verification checklist** (`GO_LIVE.md`): signup 201 → payment step → activate → login → provision Commerce tenant → POS sale → KDS ticket. `CYCOM_DEV_AUTH=0` everywhere.
- [ ] **Confirm the two payroll rates** (SA scheme, UAE national %).
- [ ] Decide launch billing: **manual invoice** vs. wire **one gateway** (HyperPay/PayTabs). Keep it simple.
- [ ] Sales: identify 5–10 **friendly JO F&B/retail prospects**; book demos on the seeded café/KDS environment.
- [ ] Draft launch pricing (tier price points) using §4 framework.

### Days 31–60 — Land & onboard the first paying customer
- [ ] **Hand-provision** the first customer's tenant; onboard them personally via `/setup` (Commerce template).
- [ ] Get them **live on real POS + KDS + inventory + local payroll/books**; bill via chosen method; **tenant flips active on real payment**.
- [ ] Capture a **case study + testimonial + reference call** willingness.
- [ ] Fix whatever the first real customer surfaces (expect onboarding + edge-case bugs).
- [ ] Begin **self-serve hardening**: wire one live payment gateway; smooth signup→pay→provision so the *next* customer needs less hand-holding.

### Days 61–90 — Self-serve on + pipeline building
- [ ] Open **self-serve signup → pay → auto-provision** for the Commerce template to a controlled set of prospects.
- [ ] Land **customer #2–#3** (mix of hand-held and self-serve to compare friction).
- [ ] Start the **RTL/Arabic** workstream in earnest (gate for SA/UAE expansion).
- [ ] **Spec the hosting platform** (§6) — scope the smallest version that removes per-customer manual ops; schedule the build.
- [ ] **Broaden messaging** from "Commerce ERP" toward multi-module, backed by the reference customer.
- [ ] Kick off the **CyMed readiness pass** (separate track) so vertical #2 has a real launch date.

**Definition of a successful 90 days:** production is live and verified; **at least one paying Commerce customer is happily live** and willing to be a reference; self-serve signup→pay→provision works for real; the hosting platform is scoped; and the founder has real onboarding-throughput and pricing data to plan the next quarter — *without any invented revenue targets driving the plan.*

---

## Appendix — assumptions the founder must fill

This plan intentionally leaves the numbers to the founder. Fill these before any financial model:
1. **Price points** per tier (Starter/Professional/Enterprise), and per-location vs per-user basis.
2. **Market sizing inputs**: SMB counts and F&B/retail share per country (JO/SA/UAE) from national statistics/registries.
3. **Onboarding throughput**: how many customers one person can land + onboard per week while high-touch.
4. **Cost base**: hosting/infra per tenant, gateway fees, support cost per account.
5. **Payment gateway choice** and its regional coverage/fees.
6. **The two payroll rates** flagged for confirmation.
7. **Target for "reference customer"** date — the single milestone the whole plan pivots on.
