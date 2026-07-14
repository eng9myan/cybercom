# CyberCom

Integrated CyberCom ecosystem monorepo.

## Layout

- `cycom/` — ERP (Odoo 19 distribution + custom Next.js front end). Imported from `eng9myan/CyCom`.
- `cyshop/` — Retail/restaurant platform (Django + Next.js). Imported from `eng9myan/Cyshop`.
- `cymed/` — Healthcare platform: hospital, clinic, laboratory, pharmacy, imaging modules (Django). Imported from `eng9myan/CyberCom-Platform-Archived` (products.cymed subset).
- `website/` — Unified CyberCom marketing site covering all products. Branding/UI/UX carried over from `eng9myan/Cybercom-Website`.

Each product keeps its own runtime (Odoo, Django, Next.js) and is independently deployable.
This repo consolidates history from prior standalone repos via `git subtree` — see individual
subdirectory history with `git log -- <dir>`.

See `docs/audit/` for the Phase 0 repository audit and `docs/roadmap/` for the implementation plan.
