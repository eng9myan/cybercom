# products.cycom.simulations

Deterministic operational simulations that seed a cycom **demo tenant** with a
realistic week of trading. Writes ordinary business records (logistics
shipments / delivery orders / routes, sales orders, manufacturing orders);
`SimulationRun` is the only simulation-owned model.

## Courier scenario — two-person last-mile operation

```
python manage.py seed_courier_sim --wipe
python manage.py seed_courier_sim --scenario surge --wipe
python manage.py seed_courier_sim --scenario van_breakdown --wipe
python manage.py seed_courier_sim --scenario route_optimization --wipe
```

One hub, one van, two employees who sort and drive. Generates parcel intake →
sort → route → deliver → POD / exception → returns into the `logistics` tables
(`DeliveryOrder`, `Package`, `Route`, `RouteStop`, `DeliveryEvent`). KPIs:
on-time %, first-attempt success, transit time p90, km per parcel, load + driver
utilisation, cost per parcel.

## Anabtawi scenario — diversified sweets business

```
python manage.py seed_anabtawi_sim --wipe
python manage.py seed_anabtawi_sim --scenario peak_export --wipe
python manage.py seed_anabtawi_sim --scenario raw_shortage --wipe
python manage.py seed_anabtawi_sim --scenario plant_downtime --wipe
python manage.py seed_anabtawi_sim --scenario retail_promo --wipe
```

Three connected lines — a plant producing oriental sweets in batches, a 4-branch
retail network, and consolidated international shipments to SA / AE / US / DE.
Writes `ManufacturingOrder` + `BillOfMaterial` (recipes over ~11 raw materials),
retail `SalesOrder`s, and export `Shipment` / `DeliveryOrder` / `Package`
(cartons with net + tare + gross weight, Incoterms, customs events). KPIs:
production yield, QC defect %, raw-material shortage impact, retail revenue by
branch, export on-time %, consolidation ratio, freight per kg, gross margin.

Common flags: `--seed`, `--start-date`, `--days`, `--scale`, `--slug`, `--wipe`,
`--dry-run`, `--out`, `--no-files`.

## Layout

```
scenarios/courier.py     scenarios/anabtawi.py       data-only scenario definitions
engine_courier.py        engine_anabtawi.py          deterministic simulators, no DB
seeder_courier.py        seeder_anabtawi.py          write a SimResult into cycom tables
kpis_courier.py          kpis_anabtawi.py            KPI rollup + CSV/JSON export
management/commands/seed_courier_sim.py, seed_anabtawi_sim.py
```

The courier + Anabtawi export flows both use `products.cycom.logistics`
(`Shipment` / `DeliveryOrder` / `Package` / `Route` / `DeliveryEvent`), the
outbound pack-and-dispatch domain added alongside this app.
