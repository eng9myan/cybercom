# CyMed × Specialized Hospital Amman — Demo Runbook

**Version:** 1.0
**Date:** 2026-08-19
**Owner:** Demo lead

---

## Prerequisites

```bash
cd D:/cybercom/cymed
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY=dev-unsafe
# SQLite mode for the local demo box
python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='core.settings'
os.environ['DJANGO_DEBUG']='True'; os.environ['DJANGO_SECRET_KEY']='dev-unsafe'
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':'dev_smoke.db'}}
django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
call_command('seed_specialized_hospital', '--patient-count=200', '--encounter-count=300')
"
USE_SQLITE=1 python tools/demo/scenarios_specialized_hospital.py
# then open tools/demo/demo_portal.html in a browser
```

Expected seed output:
```
=============================
 Specialized Hospital Amman
 Demo tenant seeded OK
=============================
 Tenant:            <uuid>
 Facilities:        8
 Practitioners:     60
 Patients:          200
 Encounters:        300
 Total billed:      ~410,000 JOD
 Total paid:        ~290,000 JOD
=============================
```

## 30-minute investor / hospital demo

| Min | Screen | Talking points |
|---|---|---|
| **0–3** | Slide / Elevator | Jordan private-tertiary landscape · Specialized Hospital's Cardiac CoE (JCI CCPC 1st JO, 7th globally) · gap: no online booking, no native patient app, no real-time insurance, no ambient scribe, no cross-provider referral inbox |
| **3–7** | `demo_portal.html` → **Reception** tab | 265-bed live occupancy, today's queue, 21-OR grid, 28 NICU incubators, ED inflow, JOD KPIs |
| **7–12** | Reception → **Clinician Workstation** tab | Pick ER chest-pain patient, order ECG + troponin, sepsis CDSS alert fires (qSOFA 2/3), admit to CCU-04 — runs Scenario 1 |
| **12–16** | **Payment & Insurance** tab | Aman TPA statin sale, real-time adjudication button, 80% covered → JoFotara e-receipt stamped — runs Scenario 7 |
| **16–20** | **Patient Portal** tab (mobile view) | NFC tap emergency profile served offline (blood O+, allergies, meds) · e-Rx refill metformin · home delivery ETA — Scenarios 8 + 3 |
| **20–24** | **Command Center** tab | AI triage flags ICH on trauma CT → HITL queue → radiologist final read 4m 12s → neurosurgery paged — Scenario 4 |
| **24–28** | **Command Center** → RCM widget | MedNet CARC-4 denial → predictor scores 0.87 → coder review → appeal composed → resubmitted approved partial — Scenario 9 |
| **28–30** | **Command Center** → Executive | DSO, first-pass yield, ED wait, 21-OR utilisation, denial rate, MRFF alignment (ai-diagnostics + population-health + ambient-scribe) |

## 60-minute deep-dive extension

- **NICU** — 28-incubator dashboard, growth curves, parent app
- **IVF** — cycle #A2601 provisioning, hormonal panel, retrieval OR — Scenario 2
- **Cross-referral** — cardiology → cath lab via ecosystem.referral_routing — Scenario 5
- **Home phlebotomy** — book slot, phlebotomist assigned, OTP proof, result released — Scenario 6
- **DTC** — Wellness Comprehensive kit → dispatch → activate → results → teleconsult — Scenario 10
- **Medical-tourism concierge** — inbound patient onboarding, cost estimate, visa letter, follow-up
- **Population-health registry** — cardiac AMI/HF outcomes sustaining JCI CCPC re-certification

## Q&A / rebuttals

| Objection | Response |
|---|---|
| "We already have HIS X" | Data migration playbook (`docs/onboarding/DATA_MIGRATION_PLAYBOOK.md`) + parallel-run mode; pilot the outpatient booking + patient app first, keep HIS X for inpatient during transition |
| "Data must stay in Jordan" | On-prem or JO-region cloud; single-tenant deploy manifest (`deploy/k8s/base/`); JO PDPL alignment in `docs/security/THREAT_MODEL.md` |
| "Staff won't adopt this" | 90-day pilot + 2-week hypercare + role-based training decks (`docs/onboarding/TRAINING_DECK_OUTLINE.md`) |
| "Prove it works" | Pilot success matrix in `docs/commercial/PILOT_AGREEMENT.md` — measurable SLIs |
| "JCI concerns" | Every workflow maps to CBAHI/JCI standards (`docs/regulatory/CBAHI_ALIGNMENT.md`) |
| "Pricing" | Point at `docs/commercial/PRICING.md`; pilot tier available |

## What NOT to promise

- SFDA / CBAHI / CCHI accreditation held by *us* — we align, we don't certify.
- Live payment gateway credentials — sandbox only in demo.
- Real WHO ICD-11 API key — sandbox client used in demo.
- Real NPHIES production cert — sandbox only.
- HSM-backed key material — dev keystore only in the demo.
- Real clinical validation study — plan documented, not executed.

Everything above is on the `docs/hardening/HARDENING_REPORT.md` outstanding-blockers list.

## Files delivered

| Purpose | Path |
|---|---|
| Hospital research profile | `docs/demo/SPECIALIZED_HOSPITAL_AMMAN_PROFILE.md` |
| Django seed command | `products/cymed/commercial/licensing/management/commands/seed_specialized_hospital.py` |
| 10 end-to-end scenarios | `tools/demo/scenarios_specialized_hospital.py` |
| Demo portal HTML (5 tabs, EN/AR) | `tools/demo/demo_portal.html` |
| Jordanian data pool | `tools/demo/data/names_jo.py`, `imaging_menu.py`, `lab_menu.py`, `lab_packages.py` |
| This runbook | `docs/demo/DEMO_RUNBOOK.md` |
| Demo status | `docs/demo/DEMO_STATUS.md` |
