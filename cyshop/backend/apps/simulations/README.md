# apps.simulations

Deterministic operational simulations that seed a cyshop **demo tenant** with a
realistic week of trading, so a prospect logging into the demo sees a business
that is actually running — sales, queues, inventory, deliveries, staff — instead
of empty screens.

The simulation writes **ordinary business records** into the real tables
(`PosOrder`, `StockMovement`, `PurchaseOrder`, `hr.Employee`, …). The only
simulation-owned model is `SimulationRun`, a manifest of what each run produced
(seed, parameters, KPI rollup, record counts) so a run can be wiped and replayed
byte-for-byte.

## QSR scenario — "McDonald's-style", 4 countries x 4 branches

```
python manage.py seed_qsr_sim --wipe                     # baseline week, full volume
python manage.py seed_qsr_sim --scenario promo_week --wipe
python manage.py seed_qsr_sim --scenario supply_disruption --wipe
python manage.py seed_qsr_sim --scenario staffing_shortage --wipe
python manage.py seed_qsr_sim --scenario import_delay --wipe
```

Useful flags:

| flag | default | meaning |
|---|---|---|
| `--scenario` | `baseline` | `baseline`, `promo_week`, `supply_disruption`, `staffing_shortage`, `import_delay` |
| `--seed` | `20260905` | RNG seed — same seed + args ⇒ identical data |
| `--start-date` | 7 days ending yesterday | `YYYY-MM-DD`, the first simulated day |
| `--days` | `7` | length of the simulated window |
| `--volume` | `1.0` | demand multiplier — `0.2` for a fast small run, `1.0` for a full busy week (~80k orders) |
| `--countries` | all | comma list of ISO codes, e.g. `JO,AE` |
| `--subdomain` | `qsr-demo` | demo tenant subdomain |
| `--wipe` | off | delete this tenant's prior operational data first (master data is kept) |
| `--dry-run` | off | run the engine + KPIs and write the CSVs, but do not touch the DB |
| `--out` | `cyshop/simulation_output/qsr-<scenario>-<date>/` | KPI export directory |

### What it generates

- **Geography** — 4 `Company` rows (Jordan, Saudi Arabia, UAE, Egypt), 4 `Branch`
  each, a `Warehouse` + stock locations per branch.
- **Menu** — ~14 sellable `KIT` products with a real bill of materials over ~25
  raw goods; selling an item consumes its components.
- **Sales** — paid `PosOrder`s across POS / kiosk / drive-thru / online, each with
  kitchen timing (`placed_at`, `prep_started_at`, `ready_at`, `served_at`) and a
  `daypart`, grouped under a `PosSession` per cashier per day.
- **Inventory** — opening balances, daily aggregated BOM consumption, daily
  spoilage, and `StockLevel` kept correct throughout.
- **Purchasing** — 5 suppliers per country with lead times and delivery
  calendars; automatic replenishment `PurchaseOrder`s + `GoodsReceipt`s, plus
  open POs still in transit at week's end.
- **Staff** — `hr.Employee` rows per branch (managers, cashiers, kitchen,
  drive-thru, cleaners, maintenance).

### Scenario variants

| variant | injected disruption |
|---|---|
| `baseline` | none |
| `promo_week` | daily lunch discount on the Big Mac Meal, with a demand uplift |
| `supply_disruption` | fries potato + buns short at JO-B2 and SA-B3 on days 3–4 |
| `staffing_shortage` | EG-B1 loses 40% of kitchen crew on days 5–6 (prep times stretch) |
| `import_delay` | cola syrup stuck at a UAE port on day 2 (all AE branches) |

### KPI output

`kpi_summary.json` plus CSVs (`orders_by_branch_day`, `orders_by_hour`,
`menu_mix`, `inventory_by_branch_sku`, `deliveries`) land in `--out`. The same
summary is stored on `SimulationRun.summary`. Headline metrics: net sales, avg
check, on-time service level by channel, wait-time p90, waste %, tightest
days-of-cover, labour % of sales, and a CSAT proxy.

## Module layout

```
scenarios/qsr.py   geography, menu + BOM, suppliers, staffing, demand shape, variants
engine.py          QsrSimulator — deterministic; no DB. Returns a SimResult.
seeder.py          QsrSeeder — writes a SimResult into the cyshop tables.
kpis.py            QsrKpis — rollup + CSV/JSON export off the SimResult.
models.py          SimulationRun
management/commands/seed_qsr_sim.py
```

Adding another scenario (logistics, hospital, …) means a new `scenarios/*.py`,
`*_engine`/`*_seeder` pair, and a `seed_*_sim` command — `SimulationRun` and the
KPI-export pattern are shared.
