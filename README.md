# CyberCom

Integrated CyberCom ecosystem monorepo.

## Layout

- `cycom/` — ERP (Odoo 19 distribution + custom Next.js front end). Imported from `eng9myan/CyCom`.
- `cyshop/` — Retail/restaurant platform (Django + Next.js). Imported from `eng9myan/Cyshop`.
- `cymed/` — Healthcare platform: hospital, clinic, laboratory, pharmacy, imaging modules (Django). Imported from `eng9myan/CyberCom-Platform-Archived` (products.cymed subset).
- `cymart/` — Marketplace orchestration layer (Django). New in Phase 3 — commission engine so far; cart/checkout/order orchestration/settlement still to come.
- `website/` — Unified CyberCom marketing site covering all products. Branding/UI/UX carried over from `eng9myan/Cybercom-Website`.
- `platform/` — Shared cross-product layer: CyIdentity, tenant, audit, events (outbox), notifications, API framework. Used by `cymed` and `cymart` today; `cyshop`/`cycom` federation is planned but not yet wired (see `docs/architecture/IDENTITY_FEDERATION.md`).
- `shared/` — Lightweight cross-cutting utilities (CyIdentity JWT auth middleware, audit logger, event base, design tokens) that don't need a full Django app.

Each product keeps its own runtime (Odoo, Django, Next.js) and is independently deployable.
This repo consolidates history from prior standalone repos via `git subtree` — see individual
subdirectory history with `git log -- <dir>`.

See `docs/audit/` for the Phase 0 repository audit, `docs/roadmap/` for the implementation plan, and
`docs/api/` for the API/event standards `platform/` actually implements (verified against code, not aspirational).
