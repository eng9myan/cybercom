# CyMed × Specialized Hospital Amman — UAT / QC Test Plan

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom demo lead
**Client:** Specialized Hospital Amman — QC audit team

---

## What this is

Structured user-acceptance test plan for the CyMed demo build. Every module in the demo is listed with:
- **What to look at** — screen area or feature
- **How to check** — click / read / try
- **Expected** — what should be true
- **Pass / Fail / N/A** — client marks

The demo is at:
**https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656**

Use the header toggles: **EN ↔ AR** (RTL) · **☀ light / ☾ dark / ⌂ system** · **A- / A / A+** font size.
Sidebar has 10 collapsible groups and 39 modules. Click any group heading to expand/collapse.

---

## Global checks (do these first)

| # | What | How | Expected | ✓ |
|---|---|---|---|---|
| G-01 | Language switch | Click **عربي** in header | All text flips to Arabic. Layout flips right-to-left. Fonts use IBM Plex Sans Arabic. | ☐ |
| G-02 | Theme | Click **☾** | Whole page turns dark. No white flashes, no unreadable text. | ☐ |
| G-03 | System theme | Click **⌂** | Follows OS theme. If OS is dark → dark; if light → light. | ☐ |
| G-04 | Font | Click **A+** | All text visibly larger, layout does not break. | ☐ |
| G-05 | Mobile view | Open URL on phone | Sidebar becomes top-strip, cards stack vertically, no horizontal scroll. | ☐ |
| G-06 | RTL + dark combined | AR + ☾ | Bidirectional layout, dark palette, still readable. | ☐ |
| G-07 | Tenant chip | Header left | Reads "Specialized Hospital · Amman · JO · JOD" plus JCI ×6, Cardiac CoE, 265 beds, 21 ORs. | ☐ |
| G-08 | Keyboard focus | Tab through | Every button shows a visible focus ring. | ☐ |
| G-09 | Reduced motion | OS setting on | No animations. | ☐ |
| G-10 | Offline | Kill Wi-Fi and reload | Page still renders — all data bundled. | ☐ |

---

## Module-by-module checklist

Each module has 3-5 concrete checks. Total ~150 checks.

### Group A — Reception & access

**A1. Reception & flow**
- [ ] 5 KPI tiles show real numbers with delta pills (up/down/flat)
- [ ] 21-OR grid shows 21 cells with mixed busy/turnover/free
- [ ] NICU grid shows 28 incubators including 2 critical (red) and empty slots
- [ ] Today's appointments table lists 8 rows with real Jordanian names + insurer chips
- [ ] Ward-occupancy bars sum to 10 wards with % values

**A2. Kiosk / self-check-in**
- [ ] 6 kiosk cells visible with status (free/busy/maint)
- [ ] Live check-in stream shows time-stamped entries
- [ ] Consent-capture table maps consents to JCI standards (IPSG-3, IPSG-4, QPS-8)

**A3. Appointment booking**
- [ ] Top specialties bars sum to 8 specialties
- [ ] Slot-availability table shows 5 specialties with in-clinic/home/tele slots
- [ ] Channel mix bars visible

### Group B — Emergency & inpatient

**B1. Emergency department**
- [ ] 5 KPI tiles including STEMI door-to-balloon
- [ ] 16-bay board with mixed ESI levels + trauma
- [ ] Triage queue table with 6 patients, ESI pills coloured correctly

**B2. Bed management / ADT**
- [ ] Movements feed shows admit / transfer / discharge / bed-hold entries
- [ ] Ward occupancy bars with `occupied/total` labels

**B3. Nursing / e-MAR**
- [ ] Next-hour e-MAR table with 5-rights verification pills
- [ ] Vitals-capture outstanding feed (sepsis re-check overdue, BP recheck, pain reassessment)
- [ ] Care plans table with compliance %

**B4. ICU**
- [ ] 16 ICU beds with mix of vent/prone/sepsis/CABG
- [ ] Ventilator settings table with FiO₂, PEEP, TV/RR, SpO₂
- [ ] Active drips table listing norepi, propofol, fentanyl, insulin, amiodarone

**B5. Operating rooms + anaesthesia**
- [ ] Theatre schedule table with 9 rooms × 5 time-blocks
- [ ] Instrument-tray CSSD status grid with 10 tray sets (one critical/fault)
- [ ] PACU 12-slot grid

**B6. Maternity + NICU**
- [ ] 28-incubator NICU grid
- [ ] LDR-in-labour table with 4 mothers, GA, stage, provider
- [ ] NICU alerts feed showing bradycardia + feed intolerance

**B7. Discharge & home care**
- [ ] Ready-to-discharge queue with blockers listed
- [ ] Home-care roster showing team, visits, region, ETA

### Group C — Clinical

**C1. Clinician workstation**
- [ ] Ahmad Al-Zoubi patient banner with insurance chip, allergy pill, anticoag pill
- [ ] Vitals grid with HR sparkline, coloured warn/crit for BP/SpO₂/temp
- [ ] Orders-in-flight table + Recent results table

**C2. Referrals & consults**
- [ ] Referral activity feed with 5 mixed items (accept/reject/close/cross-border)
- [ ] Referral-network heat bars summing to 100%

**C3. Telemedicine**
- [ ] Live sessions table with 5 sessions + session-status pills
- [ ] Session channels bar chart

**C4. CDSS + AI alerts**
- [ ] Alerts feed with sepsis-crit, ICH-crit, renal-dose-warn, drug-interaction-warn
- [ ] AI-models-in-production table (Aidoc, Rapid, Annalise, Rayvolve, Lunit) with deployment %

**C5. Ambient scribe**
- [ ] Draft SOAP note for Ahmad Al-Zoubi with S/A/P sections
- [ ] Sign & Edit buttons visible
- [ ] Latest sessions table

### Group D — Ancillary diagnostics

**D1. Laboratory**
- [ ] Worklist bars for 8 disciplines
- [ ] Recent-results table with critical-flag pills, WhatsApp/portal channel
- [ ] Analyser status grid with Cobas/Sysmex/ACL/BacT/FilmArray

**D2. Radiology / imaging + PACS**
- [ ] Modality worklist table 8 rooms including CT flagged for ICH
- [ ] Reporting queue by radiologist
- [ ] Image-share-links feed showing external/patient/med-tourism/RMS

**D3. Blood bank + transfusion**
- [ ] Inventory-by-group table (O/A/B/AB × +/-) with 4 product types
- [ ] Active transfusions feed including MTP

**D4. Pathology / histopath**
- [ ] Case workflow table listing 5 cases with stage

### Group E — Pharmacy

**E1. Pharmacy**
- [ ] Adherence/dispense stream feed showing ISMP high-alert intercept
- [ ] Robotic ADC grid — Pyxis, Omnicell, Parata, Kirby-Lester
- [ ] Formulary spend bars
- [ ] POS table with real insurer chips + JOD amounts

### Group F — Revenue & finance

**F1. Billing & insurance**
- [ ] Claims stream table with 8 claims across 8 different insurers
- [ ] Real-time adjudication card — click **Request adjudication** button
- [ ] After 700ms, result panel appears showing Aman TPA sandbox result, latency 412ms, JoFotara stamp
- [ ] Payer mix bars

**F2. Claims & denials**
- [ ] Top denial-reasons table with CARC/RARC codes
- [ ] Appeal queue feed

**F3. Finance / GL / AP / AR**
- [ ] Cash movements table with 5 rows (card, insurance, cash, EFT, JV)
- [ ] AP top-vendors bar chart
- [ ] e-Invoice archive KV list showing JoFotara/ZATCA/S3/retention/hash-chain

**F4. Payroll & benefits**
- [ ] Payroll close feed for Feb
- [ ] Benefits breakdown bars

### Group G — Operations & support

**G1. Inventory & supply chain**
- [ ] Below-par table auto-PO-ready with 6 SKUs
- [ ] Expiries feed (adenosine crit, rocuronium warn, blood tube warn)
- [ ] Cold-chain table with 6 sites, breach counts

**G2. Procurement & vendors**
- [ ] Open RFQs table (MRI service, sutures, cleaning, IT)
- [ ] Vendor performance scorecard

**G3. CSSD / sterilization**
- [ ] Autoclave 6-cell status grid including BD fail
- [ ] Trays-in-flight table

**G4. Biomedical engineering**
- [ ] Open tickets table with SLA-approaching / breach pills
- [ ] PM schedule for next 7 days

**G5. Facilities & housekeeping**
- [ ] Housekeeping stream (turnover, terminal clean, spill)
- [ ] Work orders open table

**G6. Food services / diet**
- [ ] Diet-order distribution bars
- [ ] Kitchen tickets in-progress including enteral/warfarin-diet notes

### Group H — Workforce & governance

**H1. HR & credentialing**
- [ ] Licenses expiring < 60d table with renewal-status pills
- [ ] Training compliance table mapping to JCI standards

**H2. Rota / scheduling**
- [ ] On-call today table with 6 specialties, consultant, registrar, backup
- [ ] Fair-share metrics bars

**H3. Quality & incidents**
- [ ] Recent events feed with ISMP intercept, med delay, fall risk
- [ ] JCI/CBAHI KPI table with 6 standards all ✓

**H4. Infection prevention**
- [ ] Active isolations table (MRSA, CRE, flu, neutropenic)
- [ ] Antimicrobial spend bars

**H5. Medical records**
- [ ] RoI queue table
- [ ] ICD-10 coder productivity bars

**H6. Marketing & engagement**
- [ ] Active campaigns table (5 campaigns across SMS/WA/Email)

### Group I — Patient-facing

**I1. Patient app / portal**
- [ ] Upcoming visits feed
- [ ] Active prescriptions feed
- [ ] My bills table with JOD + insurance-paid split
- [ ] NFC / emergency card KV panel (blood type, allergies, meds, DNR, organ donor)

**I2. Delegated access / family wallet**
- [ ] Recent delegated payments feed (AED, SAR, USD → JOD)

**I3. Loyalty / membership**
- [ ] Bundles-available table with JOD prices
- [ ] Top redemptions bars

**I4. Medical tourism concierge**
- [ ] Live tourism cases (Riyadh, Baghdad, Sana'a, Dubai, Erbil)
- [ ] Concierge services chip cloud with 8 services

### Group J — Executive

**J1. Command center**
- [ ] 5 KPI tiles (occ, ED wait, OR util, DSO, first-pass yield)
- [ ] Ops alerts feed with ICH, CCU capacity, OR turnover, MedNet denials
- [ ] MRFF alignment table with 4 rows all live/beta
- [ ] Department occupancy bars

**J2. Executive dashboards**
- [ ] Revenue by service line bars
- [ ] CMO clinical outcomes table with better/above benchmarks
- [ ] CFO financials table

**J3. Population health**
- [ ] Cardiac AMI registry table
- [ ] IVF cycle registry by age band

**J4. Regulatory alignment**
- [ ] Standards mapping table with JCI/CBAHI/CCHI/SFDA rows
- [ ] Next audit windows feed

---

## Sign-off block

**Client audit team**

| Role | Name | Date | Signature |
|---|---|---|---|
| CIO / IT Director | | | |
| Medical Director | | | |
| Nursing Director | | | |
| Head of RCM / Finance | | | |
| Quality / JCI Officer | | | |

**Overall verdict:**
- [ ] Pass — proceed to paid pilot
- [ ] Conditional pass — issues to fix listed below, retest after
- [ ] Fail — return to design

**Comments / open findings:**

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

---

## Notes for the client

- **This is a demo, not the production system.** The 10 modules with a "REAL" flag in the note above run against actual seeded data. All others show representative screens grounded in Specialized Hospital's real world (265 beds, 21 ORs, 11 accepted payers, JCI Cardiac CoE).
- **What's stubbed** — real-time NPHIES / JoFotara / HyperPay / WHO ICD-11 calls are sandboxed. Documented in `docs/demo/DEMO_STATUS.md`.
- **Data privacy** — no real patient data is present. All names, MRNs, national IDs are synthetic.
- **Feedback channel** — email findings + this checklist to Cybercom lead; alternatively leave inline comments on any element in the artifact viewer.
- **Full audit against live backend** — schedule a Zoom walkthrough; Cybercom will run the seed + 10 end-to-end scenarios + expose the API through Swagger UI at `/api/docs/`.
