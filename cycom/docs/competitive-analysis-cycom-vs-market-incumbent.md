# Cycom ERP — Competitive Positioning Analysis (Internal)

**Scope note:** This compares Cycom's real, current module set (verified against this repo's actual code, not marketing copy) against general knowledge of the incumbent open-core ERP category Cycom's Sofia Platform competes in. Specific pricing/AI-credit claims below reflect the vendor's publicly known commercial model as of general knowledge, not a live-verified current price sheet — confirm exact current numbers before using this externally.

## 1. Core Financials & Localization

Cycom's real strength: **accounting/GL, AR/AP, HR/payroll, and now Manufacturing/MRP and Subscriptions are ground-up implementations on Cycom's own multi-tenant Sofia Platform** (real double-entry ledger via `products/cycom/accounting/services.py::post_journal_entry`, verified live tonight with real balanced-entry tests). No dependency on a third-party engine's release cycle for core financial logic — Cycom controls its own accounting roadmap directly.

The incumbent's model bundles localization packs per country as separate, often community-vs-enterprise-gated modules — a real friction point for multi-region deployments where some localizations are enterprise-only.

## 2. Advanced Logistics & Warehouse Management

Cycom Inventory (`products/cycom/inventory/`) implements weighted-average costing, multi-warehouse stock moves, and now (as of tonight) Manufacturing/MRP with BoM-driven component consumption and WIP-clearing GL posting — a real, working chain from raw-material consumption to finished-goods capitalization, verified with actual balanced-ledger tests.

Gap acknowledged honestly: Cycom does not yet have cluster-picking or multi-step wave-picking UI workflows. This is real, unclaimed scope — worth a dedicated slice if warehouse throughput at scale becomes a priority, not something to paper over.

## 3. Automation & Intelligent Pipelines

This is genuinely Cycom's strongest differentiator right now, not a gap: the **CyAI platform** (`cyai_memory`, `cyai_reports`, `cyai_moduledev`, `cyai_analytics`, `cyai_platform`) is a real, built, deployed multi-agent AI layer — natural-language reporting, a local memory agent, and a module-developer agent with a real security/approval gate before any AI-generated code ships. This isn't a bolt-on chatbot; it's integrated into the same tenant/auth model as every other module.

The incumbent's AI features are typically metered per-document/per-call against a hosted cloud service — a real, ongoing operating cost that scales with usage. Cycom's CyAI stack runs against the tenant's own configured model provider (`ModelGateway`, real Anthropic SDK wiring already built), which is a structurally different cost model: no per-document toll on your own data.

## 4. Honest Structural Weaknesses Worth Naming in the Incumbent's Model (General Knowledge, Not Live-Verified)

1. **Upgrade friction across major versions** — a long-documented pain point in that ecosystem; breaking changes across major version boundaries routinely require paid migration services or significant in-house engineering time.
2. **Community vs. Enterprise feature gating** — several accounting/localization/multi-company features are enterprise-license-only, which becomes a real cost cliff as a deployment grows.
3. **AI-feature metering** — hosted-AI features in that ecosystem are typically credit-metered per document/call, an ongoing variable cost that scales with document volume, not a one-time engineering cost.
4. **Deep customization still requires developer tooling** — the low-code layer covers UI/workflow tweaks well, but real new business logic still needs actual code changes, same as any platform including Cycom's own module-dev tooling.

## 5. Where Cycom Should Invest Next (Roadmap, Not Yet Built)

- **Self-hosted OCR extraction worker pool** — see `docs/proposals/ocr-worker-pool-blueprint.md` (companion doc) for a concrete architecture: queue-based worker pool (Celery, already a dependency), pluggable OCR backend (start with an open-source model, keep the interface provider-agnostic so a hosted API can be swapped in later), landing into the existing `Documents` module's generic linked-record pattern. Real, buildable, not yet built.
- **Pre-aggregated reporting layer for fast ad-hoc financial pivots** — a materialized/indexed summary table refreshed on journal-entry post (not on every read), avoiding the query-time cost of scanning raw journal lines for every pivot. Concrete design in the companion doc below.
- **Cluster/wave picking UI** — real gap, not yet scoped in detail.

Both blueprint items below are illustrative architecture + starter code, not wired into `core/urls.py` yet — they're a next-phase proposal, matching this project's own "design before building" discipline for anything touching new cross-cutting infrastructure.
