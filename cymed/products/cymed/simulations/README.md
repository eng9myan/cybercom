# products.cymed.simulations

Deterministic operational simulation that seeds a cymed **demo tenant** with a
realistic week of a hospital + clinic network running, so a prospect logging in
sees a working hospital instead of empty screens. Writes ordinary clinical
records (encounters, ED visits, admissions, bed assignments, orders/results);
the only simulation-owned model is `SimulationRun`.

## Hospital scenario — "Cymed US Specialty Hospital" (Amman) + 5 clinics

```
python manage.py seed_hospital_sim --wipe
python manage.py seed_hospital_sim --scenario ed_surge --wipe
python manage.py seed_hospital_sim --scenario imaging_ct_downtime --wipe
python manage.py seed_hospital_sim --scenario nurse_shortage --wipe
python manage.py seed_hospital_sim --scenario pharmacy_stockout --wipe
```

| flag | default | meaning |
|---|---|---|
| `--scenario` | `baseline` | `baseline`, `ed_surge`, `imaging_ct_downtime`, `nurse_shortage`, `pharmacy_stockout` |
| `--seed` | `20260905` | same seed + args ⇒ identical data |
| `--start-date` | 7 days ending yesterday | `YYYY-MM-DD` |
| `--days` | `7` | window length |
| `--scale` | `1.0` | volume multiplier (`0.15` = fast run) |
| `--slug` | `cymed-hospital-sim` | demo tenant slug |
| `--wipe` | off | delete this tenant's prior clinical data first |
| `--dry-run` | off | run engine + KPIs + files, no DB writes |

### What it generates

- 1 hospital facility (10 wards, ~230 beds) + 5 clinic facilities, ~150 providers
  across 12 specialties, a patient pool.
- **Emergency**: `EmergencyVisit` + `EmergencyTriage` (ESI) + `EmergencyDisposition`,
  crowding-driven waits and LWBS.
- **Clinics**: `Appointment` + `Encounter` per session slot, no-shows, walk-ins.
- **Inpatient**: `Encounter` + `Admission` + `HospitalStay` + `ICUStay` +
  `BedAssignment`, ward bed-capacity tracking (full wards board), LOS + discharge.
- **Orders**: `Order` / `OrderItem` / `OrderResult` for lab / imaging / pharmacy
  with realistic turnaround (stat vs routine, cultures separated).
- Six **service lines** (cardiac, orthopedic, obstetric, neonatal, pediatric,
  general) each with its own admit rate, LOS, ICU rate and order profile — this
  is how the "condition streams" (OB / cardiology / orthopedics / neonatal /
  pharmacy-lab-imaging) all flow through one ADT / encounter / order machinery.

### KPIs

`SimulationRun.summary` + `kpi_summary.json` + CSVs: ED door-to-provider /
door-to-disposition / LWBS / admit rate by ESI; inpatient census, bed occupancy,
ALOS, ICU census, ED boarding; order turnaround (lab / imaging / microbiology /
medication, mean + p90); clinic no-show / utilisation; per service line; CSAT
proxy.

## Layout

```
scenarios/hospital.py   geography, wards/beds, specialties, order catalogue, service lines, variants
engine.py               HospitalSimulator — deterministic, no DB
seeder.py               HospitalSeeder — writes a SimResult into cymed tables (inside tenant_context)
kpis.py                 HospitalKpis
management/commands/seed_hospital_sim.py
```
