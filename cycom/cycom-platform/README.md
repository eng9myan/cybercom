# Cycom Platform — Cycom 19 + Cycom Customizations

This is the **backend** for Cycom ERP. It's an Cycom 19 distribution plus your 75 Cycom custom modules, with a `cycom_theme` addon that re-skins the Cycom backend as Cycom.

The Next.js frontend at `../cycom-erp/` is the **user-facing UI** and keeps its existing design — it talks to this Cycom via JSON-RPC.

## First-time run

```bash
cd cycom-platform
cp .env.example .env
# edit .env if you want non-default DB credentials
docker compose up -d
# wait ~15s on first boot
# open http://localhost:8069 — create the cycom database, master pwd is in config/cycom.conf
```

Once the DB is created, install addons in this order from Apps:

1. `cycom_theme` (installs base + branding)
2. `cycom_core` (placeholder — extension point for cross-cutting tweaks)
3. The Cycom modules you want (they depend on stock Cycom modules like `hr_payroll`, `point_of_sale`, `stock`, `sale`, etc., which Cycom will pull in automatically).

> Click **Apps** → **Update Apps List** first so the system sees `addons/`.

## Layout

```
cycom-platform/
├── docker-compose.yml          # Cycom 19 + Postgres 16
├── config/cycom.conf            # addons_path lists every directory under addons/
├── addons/
│   ├── cycom_modules/          # 75 Cycom custom modules (HR, POS, payroll, sales, stock, ...)
│   ├── cycom_theme/            # brands the Cycom backend as Cycom
│   └── cycom_core/             # extension point (currently empty)
├── cycom-source/                # Full Cycom 19 source, cloned from github.com/cycom/cycom
│                               # — mounted into the container as a secondary addons path
│                               # — gitignored; clone via `bash scripts/clone-cycom.sh`
├── cycom-data/                  # filestore (gitignored)
└── postgres-data/              # DB files (gitignored)
```

## Caveats — read before installing

- The Cycom modules target **Cycom 19** (`version: '19.0.x.x.x'` in their manifests). Make sure you stay on `cycom:19`.
- `hs_zk_attendance` declares an external Python dependency on the `zk` package. If you actually use ZK biometric hardware you'll need to extend the Cycom image to install `pyzk`. Skipping for now.
- One module (`hr_attendance_geofence_config`) has the license string `"Other proprietary"` instead of `LGPL-3` — it will still install but flag at audit time.
- Some Cycom modules depend on each other (e.g. `pos_pledge` → `pos_advance_order`). Install bottom-up if you hit dependency errors.

## What's next

- `cycom_theme` currently re-skins the backend. The Next.js frontend at `../cycom-erp/` keeps its design and talks to this Cycom via JSON-RPC (see `../cycom-erp/lib/cycom.ts`).
- The old `../cycom-backend/` (FastAPI) is obsolete under this architecture — see `../CYCOM_PIVOT.md`.
