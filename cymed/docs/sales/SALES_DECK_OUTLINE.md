# CyMed Sales Deck Outline

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom sales enablement
**Audience:** CyMed sales reps preparing for CxO / CIO / Medical Director meetings
**Length:** 18 slides · target 35 minutes talk + 15 minutes Q&A

---

## How to use this outline

Read this once on the way to the meeting. Each slide gives you:

- **Headline** — the exact words on screen
- **Bullets** — what the customer reads
- **Speaker notes** — what you say out loud
- **Visual** — what to show (illustrative unless marked otherwise)

Numbers marked *(illustrative)* are pre-pilot placeholders. Replace them with the customer's own baseline once discovery is done. Never quote them as CyMed benchmarks.

Related docs:

- [Elevator pitch (EN + AR)](./ELEVATOR_PITCH.md)
- [Email templates (EN + AR)](./EMAIL_TEMPLATES.md)
- [90-day pilot pack](./PILOT_PACK.md)
- [Editions and pricing model](./EDITIONS_PRICING.md)

---

## Slide 1 — Cover

**Headline:** CyMed by Cybercom — the Middle East healthcare platform

**Bullets on screen:**

- Full-stack HIS, LIS, RIS, pharmacy, RCM
- Built for Jordan, Saudi, Emirates from day one
- 39 modules · one MRN · one platform
- Presented by: [Rep name] · [Title] · Cybercom

**Speaker notes:**
Open on the customer's name and role of the room. Thank the sponsor by name. Say once, out loud: "We are here to earn a 90-day paid pilot, not to sell a five-year contract today." That framing sets the meeting.

**Visual:** CyMed wordmark, hospital corridor photo (or the customer's own building if public), Jordan / KSA / UAE flag row along the bottom.

---

## Slide 2 — The moment

**Headline:** Three curves are converging in Middle East healthcare — right now

**Bullets on screen:**

- **Digital patient expectations:** WhatsApp-native, app-native, family-abroad-pays-the-bill
- **Regulatory tightening:** NPHIES (KSA) mandatory, JoFotara (JO) e-invoice mandatory, CCHI enforcement rising
- **Provider economics:** payer denials up, staff shortages up, medical-tourism inflow up
- **The gap:** legacy HIS platforms were built in Boston in 2004, not Riyadh in 2026

**Speaker notes:**
Do not name competitors here — name the pain. The room already lives this. Land the "built in Boston in 2004" line and pause. This is the only slide where you get to be a little provocative.

**Visual:** three rising curves on one chart — Patient expectations, Regulatory load, Cost pressure — meeting at "2026."

---

## Slide 3 — Who we are

**Headline:** Cybercom · CyMed · engineering built in-region

**Bullets on screen:**

- Cybercom: multi-vertical platform group (CyMed healthcare, Cycom ERP, CyED education, CyID identity)
- CyMed mission: one clinical + financial platform that speaks Arabic first, connects to every ME payer, runs from clinic to tertiary hospital
- Engineering: full-time Django / React / FHIR team, Amman-based, on-call in region
- Not a reseller. Not a systems integrator. We build the product.

**Speaker notes:**
"Not a reseller" is the sentence that matters. Most competitors in this room resell Cerner, Epic, or InterSystems. We own the code. That means we can build the NPHIES field they need on Tuesday and ship it Thursday.

**Visual:** Cybercom product family diagram (CyMed at center, siblings around), small team photo if available.

---

## Slide 4 — The problem in one image

**Headline:** Today's ME hospital runs on five systems that hate each other

**Bullets on screen:**

- **Clinical HIS** for the doctor
- **Separate LIS** for the lab
- **Separate PACS** for imaging
- **Separate pharmacy system** with its own inventory
- **Separate finance / RCM** bolted on via nightly CSV
- Result: no single MRN, no single ledger, no single patient view. The patient re-tells the same story four times per visit.

**Speaker notes:**
Ask, don't tell: "How many patient identifiers exist in your hospital today?" Wait. The answer is always more than one. That is the whole slide.

**Visual:** five disconnected system boxes with red dashed lines between them, a confused patient icon in the middle.

---

## Slide 5 — What CyMed is

**Headline:** One platform. One MRN. Ten module groups. 39 modules.

**Module groups on screen:**

| Group | Example modules |
| --- | --- |
| Front office | Reception, appointments, referrals |
| Emergency | ED triage, ED tracking, trauma bay |
| Inpatient | Ward, ICU, NICU, OR scheduling |
| Ambulatory | Clinic, specialty clinics, day-care |
| Diagnostics | Lab (LIS), Imaging (RIS), PACS integration |
| Pharmacy | Inpatient, outpatient, formulary, e-Rx |
| Revenue cycle | Coding, claims (NPHIES), denials, JoFotara |
| People | HR, credentialing, roster, payroll hooks |
| Governance | Quality, incidents, JCI / CBAHI / HCAC bundles |
| Digital front door | Patient app, delegated pay, exec command center |

**Speaker notes:**
Do not read the table out loud. Land the top line: one platform, one MRN, 39 modules. Then say: "You license what you need. You never integrate with yourself."

**Visual:** the 10-group grid above, with the customer's likely starting modules pre-highlighted.

---

## Slide 6 — Under the hood

**Headline:** Modern stack. Open standards. Zero vendor traps.

**Bullets on screen:**

- **Backend:** Django + PostgreSQL — auditable, mature, easy to hire for
- **Frontend:** React + Next.js — Arabic RTL native, mobile-responsive, PWA
- **Interop:** FHIR R4 for clinical data, HL7 v2 for legacy device feeds
- **Integrations shipped:** NPHIES (KSA), JoFotara (JO), Hakeem (JO national record), HyperPay, WHO ICD-11
- **Deployment:** cloud, on-prem, or hybrid — data residency in-country available (JO / KSA)

**Speaker notes:**
This slide is for the CIO in the room. Say "Postgres, not Oracle. Django, not proprietary." That is the sentence they remember. Everything else is the appendix in their head.

**Visual:** simple three-tier diagram (Frontend / Backend / Data) with integration logos along the bottom (NPHIES, JoFotara, Hakeem, HyperPay, WHO).

---

## Slide 7 — Live demo teaser

**Headline:** Five screens. Five minutes. Then we do it live.

**Bullets on screen:**

1. **Reception** — walk-in patient, Iqama / National ID lookup, insurance eligibility check in one click
2. **Clinician** — SOAP note being written by the ambient scribe while the doctor talks
3. **Pharmacy insurance** — NPHIES pre-auth on a controlled drug, real-time verdict
4. **NFC wristband** — nurse taps, sees the five-rights medication check
5. **Executive command center** — live occupancy, ED wait time, denial rate on one screen

**Speaker notes:**
This slide is the promise. The next thing you do is either open the live demo URL or the recorded demo. Do not skip the demo. If time is short, cut slides 8–11, never cut this.

**Live demo URL:** https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656

**Visual:** 5 phone / laptop screenshots in a row, numbered 1–5.

---

## Slide 8 — The Jordan story

**Headline:** Specialized Hospital Amman — flagship reference build

**Bullets on screen:**

- 21 documented gaps in the current HIS at Specialized Hospital
- CyMed closes all 21 in the Hospital edition, out of box
- JoFotara e-invoice: mandatory since 2024, live in CyMed
- Hakeem national record: bidirectional sync, live in CyMed
- Arabic-first UI: not translated, designed RTL

**Speaker notes:**
If you are in Amman, this slide is your anchor. Name Specialized Hospital only if the room already knows we are talking to them. Otherwise, say "a leading Amman tertiary hospital." Never name a prospect who has not signed a case-study release.

**Visual:** map of Jordan with Amman pinned; small table showing "Gap → CyMed module" for the top 5 of the 21.

---

## Slide 9 — The Saudi story

**Headline:** NPHIES-native. CBAHI-aligned. SFDA on the roadmap.

**Bullets on screen:**

- **NPHIES:** eligibility, pre-auth, claims — native, not a plug-in
- **CBAHI:** evidence bundles (policies, KPIs, incident logs) mapped to standards
- **SFDA:** medication traceability and controlled-substance workflow ready
- **CCHI:** payer contracts and price lists modelled in the RCM engine
- **Arabic + English:** every screen, every report

**Speaker notes:**
For KSA prospects, lead with NPHIES. It is the single most expensive integration a Saudi hospital pays for. We ship it. That fact alone earns the pilot conversation.

**Visual:** four badges in a row — NPHIES, CBAHI, SFDA, CCHI — each with a green check.

---

## Slide 10 — The ecosystem

**Headline:** CyMed Ecosystem — the network effect, not just a product

**Bullets on screen:**

- **Cross-provider referral:** send a patient with their record intact, across facilities on CyMed
- **Shared inventory / group purchasing:** for hospital groups and clinic chains
- **Loyalty and patient wallet:** one balance across every CyMed provider
- **Medical-tourism concierge:** visa letter, transfer, translator, hospital, follow-up — one workflow
- **Delegated pay:** family abroad settles a JO patient's bill from the UAE, in AED

**Speaker notes:**
This is the slide competitors cannot match. Epic does not talk to Cerner across hospitals in Amman. CyMed talks to CyMed. Name the medical-tourism angle for KSA and JO — it is real revenue for them.

**Visual:** a small network graph — 3 hospitals, 2 clinics, 1 lab, all linked, with a patient icon moving between them.

---

## Slide 11 — The AI story

**Headline:** AI baked in, not bolted on

**Bullets on screen:**

- **Ambient scribe:** doctor talks, SOAP note writes itself, Arabic + English
- **AI clinical decision support:** drug-drug, dose-by-weight, allergy, guideline nudge at point of order
- **AI imaging triage:** chest X-ray and CT head first-pass prioritization (roadmap: Q2)
- **Population health:** cohort dashboards, chronic-disease registries, risk stratification
- **MRFF-aligned research priorities:** offline-first rural, ambient scribe, AI diagnostics — universal, not Australia-only

**Speaker notes:**
The scribe is the "wow." If time allows in demo, show it live. If not, show the 45-second recorded clip. Do not oversell imaging AI — position it as roadmap, not shipped. Honesty here protects the pilot.

**Visual:** split screen — doctor talking on the left, SOAP note filling itself on the right.

---

## Slide 12 — Differentiators

**Headline:** Why CyMed, not the alternatives

| Dimension | Global (Epic / Oracle Health / Meditech) | ME regional (InfoMed / DXware / Bayanat / Alpha) | Point solutions (Cliniko / Zoho) | **CyMed** |
| --- | --- | --- | --- | --- |
| Full-stack single platform | Yes, but per-module licensing at multiples of our price | Partial (3–5 modules typical) | No (single-purpose) | **Yes, 39 modules** |
| Middle-East-native (Arabic, JOD / SAR / AED, NPHIES, JoFotara) | Retro-fitted | Yes, but often only in one country | No | **Yes, all three markets** |
| Ambient scribe + AI CDS baked in | Add-on modules, extra licensing | Rare / roadmap | No | **Included** |
| Cross-provider ecosystem | No | No | No | **Yes** |
| Patient app with delegated pay | No | Rare | No | **Yes** |
| Medical-tourism concierge | No | No | No | **Yes** |
| Cloud + on-prem + JO data residency | Cloud-only or on-prem-only | Usually on-prem-only | Cloud-only | **All three** |
| 90-day paid pilot with success criteria | No (multi-year contract first) | Rare | Free trial only | **Yes** |

**Speaker notes:**
Do not read the table. Point to the last row. Say: "Nobody in this market offers a 90-day paid pilot with written success criteria. If we do not hit them, you do not convert. That is the deal."

**Visual:** the table above, with the "CyMed" column highlighted and every green check on the same visual grid.

---

## Slide 13 — Editions and tiers

**Headline:** Five editions. Three tiers. One platform.

**Editions:**

| Edition | For | Starting module set |
| --- | --- | --- |
| Clinic | Solo and multi-doctor clinics | Reception, EMR, e-Rx, billing |
| Hospital | 20-bed to tertiary | All 10 module groups |
| Lab | Standalone LIS | Order, sample, result, invoice |
| Imaging | Standalone RIS + PACS bridge | Order, worklist, report, invoice |
| Pharmacy | Retail and hospital pharmacy | Formulary, dispense, insurance, inventory |
| Ecosystem add-on | Any of the above | Cross-provider referral, loyalty, med-tourism |

**Tiers:**

| Tier | What you get | Best for |
| --- | --- | --- |
| Pilot | 90 days, full features, capped users | Prove it on your data |
| Standard | Production, standard SLAs, cloud or single-tenant cloud | Mid-size hospital, clinic chain |
| Enterprise | Multi-site, on-prem or hybrid, custom SLAs, dedicated CSM | Large hospitals, groups, insurers |

**Speaker notes:**
The customer picks an edition and a tier. That is it. Two decisions. Do not over-explain — the deck below has the pricing model.

**Visual:** 5 edition cards in a row, then a 3-tier ladder underneath.

---

## Slide 14 — 90-day pilot mechanics

**Headline:** A paid pilot with written success criteria

**Bullets on screen:**

- **Length:** 90 days from kickoff
- **Scope:** production data, real users, capped licenses
- **Success criteria:** written and signed at day 0 (examples: NPHIES pre-auth turnaround under 60 seconds, denial rate reduced by X% vs current baseline, ambient-scribe adoption above Y% of eligible visits)
- **Price:** paid — not free — so both sides are committed
- **Credit on conversion:** 100% of pilot fee credited against year-1 subscription if the customer converts within 30 days of pilot end
- **Exit:** if pilot fails criteria, customer walks away. Data returned. No lock-in.

**Speaker notes:**
The credit-on-conversion line is the close. Say: "You are effectively paying us to prove ourselves, and if we do, the money comes back." Legal templates (MSA, BAA, DPA) are ready — no procurement stall.

**Visual:** 90-day timeline with 3 milestones (Day 0 kickoff, Day 45 mid-review, Day 90 go / no-go).

---

## Slide 15 — Compliance and certifications roadmap

**Headline:** Aligned with every certification body that matters here

| Body | Region | CyMed alignment |
| --- | --- | --- |
| JCI | International | Evidence bundles, KPI dashboards, incident logs mapped |
| CBAHI | KSA | Standards library indexed to modules |
| HCAC | Jordan | Accreditation-ready reports out of box |
| CCHI | KSA payer | Native contract and pricelist modelling |
| SFDA | KSA drugs | Traceability, controlled-substance workflow |
| NPHIES | KSA insurance | Live integration |
| JoFotara | JO e-invoice | Live integration |
| Hakeem | JO national record | Live sync |

**Speaker notes:**
The word to say is "aligned," not "certified for the customer." A hospital certifies itself. Our job is to make that certification cheap and repeatable. That is what this table says.

**Visual:** two columns — Regulatory (JCI / CBAHI / HCAC / SFDA) and Interoperability (NPHIES / JoFotara / Hakeem / CCHI) — each with badges.

---

## Slide 16 — Pricing framework

**Headline:** Pricing you can explain to your CFO in one minute

**Model, not final numbers:**

| Edition | Meter | Note |
| --- | --- | --- |
| Clinic | Per active provider per month | Provider = doctor or dentist writing notes |
| Hospital | Per active provider per month | Nurses, admin, techs are unlimited within cap |
| Lab | Per workstation per month | Analyzer bench = one workstation |
| Imaging | Per modality room per month | CT / MR / X-ray room |
| Pharmacy | Per dispensing counter per month | POS counter or hospital dispensing station |
| Ecosystem add-on | Flat per site per month | Enables cross-provider referral and loyalty |

**Discount ladder:**

- **Pilot tier:** posted rate, credited back on conversion
- **Standard tier:** posted rate
- **Enterprise tier:** volume discount, multi-site discount, multi-year discount stackable

**Speaker notes:**
Do not quote the number today unless procurement is in the room and asks. Say: "The meter is per active provider — meaning we do not charge you for the receptionist. Most competitors do." That framing is worth the whole slide.

**Visual:** the meter table above; do not put numbers on the screen.

---

## Slide 17 — Onboarding

**Headline:** 12-week onboarding. Then 90 days of hypercare.

**Weeks 1–2:** Discovery, data mapping, integration inventory
**Weeks 3–4:** Environment stand-up, SSO, network, security review
**Weeks 5–6:** Migration dry-run, master data (drug formulary, price lists, users)
**Weeks 7–8:** Configuration workshops per department, workflow validation
**Weeks 9–10:** UAT — [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69)
**Week 11:** Train-the-trainer + super-users
**Week 12:** Cutover weekend + go-live
**Weeks 13–24:** Hypercare — on-site rotation, daily standup, weekly steering

**Speaker notes:**
Point to the UAT checklist link. Say: "This is our checklist. Not a marketing brochure — the actual test cases. We will walk your team through it in the technical follow-up." Concrete beats promise every time.

**Visual:** 12-week Gantt with the 8 phases above; hypercare block shaded on the right.

---

## Slide 18 — The ask and next step

**Headline:** One decision today. One meeting next week.

**The ask:**

- **Today:** in-principle agreement to a 90-day paid pilot, subject to written success criteria
- **Next week:** 30-minute technical follow-up with your CIO and clinical informatics lead
- **Within 30 days:** signed pilot MSA + kickoff on the calendar

**What we bring next week:**

- Written success criteria draft based on today's discussion
- Legal pack: MSA, BAA, DPA templates
- Integration inventory questionnaire
- Named delivery lead and their calendar

**Speaker notes:**
Land the meeting, not the deal. Say: "We are not asking you to sign anything today. We are asking you to give us 30 minutes next week with the right technical people in the room." That is the win for this meeting. Anything more is a bonus.

**Visual:** three checkboxes stacked vertically — Today, Next week, Within 30 days — each with the exact ask.

---

## Appendix (do not present, keep in the deck)

- Reference architecture diagram
- Data flow diagram (NPHIES / JoFotara / Hakeem)
- Security controls summary
- Sample UAT test cases
- Delivery lead bios
- Redacted customer references (once available)

---

*End of deck outline.*
