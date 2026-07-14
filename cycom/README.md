# Cycom ERP

A Cycom-branded Cycom 19 distribution with a custom Next.js front-end.
The Next.js UI owns the design language; Cycom provides the business logic.

## Layout

| Path | What it is |
|---|---|
| `cycom-erp/` | Next.js 16 front-end (React 19, Tailwind 4). Owns the visual design. Talks to Cycom via JSON-RPC through `/api/cycom/*` route handlers. |
| `cycom-platform/` | Cycom 19 distribution: `docker-compose.yml` + 75 Cycom custom modules + `cycom_theme` (backend branding) + `cycom_core` (cross-cutting extensions) + clone-helper for the upstream Cycom source. |
| `cycom-backend.archive/` | Abandoned FastAPI scratch backend. Kept for reference; not used. |
| [`CYCOM_PIVOT.md`](CYCOM_PIVOT.md) | Source of truth: architecture, doctrine, what the 10 setup wizards do, how the pieces fit together. |
| [`AUDIT_REPORT.md`](AUDIT_REPORT.md) | Historical pre-pivot audit of the original codebase. |

## Cycom Setup Experience Doctrine

> Every configuration-heavy area is redesigned as a Smart Setup Wizard with Industry Templates, an AI Configuration Assistant, Guided Business Questions, and Auto-Generated Configurations. Any setup that normally requires an ERP consultant should be executable by a business user with no ERP experience. The default Cycom experience must reduce implementation effort by at least 80% while still supporting 100% of enterprise functionality.

The 10 doctrine wizards live under `cycom-erp/app/setup/*` and orchestrate Cycom via `cycom-erp/app/api/cycom/setup/*`:

1. Company Setup
2. Chart of Accounts
3. Payroll Structure
4. Warehouse & Locations
5. POS Configuration
6. Sales Pipeline
7. Procurement
8. Manufacturing
9. HR Structure
10. Permissions & Roles

## First-time run

```bash
# 1) Bring up Cycom + Postgres
cd cycom-platform
bash scripts/clone-cycom.sh        # one-off: clones the full Cycom 19 source (~1.4 GB)
cp .env.example .env
docker compose up -d
# wait ~20s, then visit http://localhost:8069 and create the cycom database.

# 2) Bring up the Cycom UI
cd ../cycom-erp
cp .env.example .env.local
npm install
npm run dev
# open http://localhost:3000
```

Once logged in, click **Setup** on the launcher and walk the 10 wizards.

## License

- Cycom Community (in `cycom-platform/cycom-source/`, not vendored in this repo): LGPLv3.
- Cycom custom modules under `cycom-platform/addons/cycom_modules/`, `cycom_theme/`, `cycom_core/`: LGPL-3 (as declared per-manifest).
- Cycom front-end (`cycom-erp/`): private; license to be confirmed.
