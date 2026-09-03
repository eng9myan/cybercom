# CyMed Sales Playbook

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom sales enablement
**Audience:** every rep touching a CyMed deal — SDR, AE, SE, CS

---

## 1. How to use this playbook

- **SDR / BDR** — sections 2, 3, 4, 6. Focus on ICP + cold outreach templates.
- **AE** — sections 2 through 12. This is your bible.
- **SE / SA** — sections 3, 6, 7, 11, plus every doc in `docs/sales/` marked "technical".
- **CS** — sections 5, 10, 14. Focus on onboarding + expansion.

Read section 2 before every first meeting. Skim section 3 weekly.

---

## 2. The 4-tier demo strategy

| Tier | Client stage | Rep type | Artefact used | Expected outcome | KPI to track |
|---|---|---|---|---|---|
| **T1 · Cold outreach** | Never heard of us | SDR | [Cloud artifact URL](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656) | 30-min discovery meeting booked | Meeting-set rate ≥ 8% |
| **T2 · Discovery Zoom** | Curious | AE | Same artifact + [`DEMO_RUNBOOK.md`](../demo/DEMO_RUNBOOK.md) 30-min script | Qualified opportunity, [tier A/B/C rubric](QUALIFICATION_SCRIPT.md) | Opp-creation rate ≥ 40% |
| **T3 · Technical demo on-site** | Serious, IT+CMO in room | SE + AE | Local Django + real API + [10 scenarios](../../tools/demo/scenarios_specialized_hospital.py) | Signed pilot MSA within 30 days | Pilot-signed rate ≥ 25% |
| **T4 · Paid 90-day pilot** | Committed | CS + engineering | Deploy to their VPC or JO cloud, [pilot playbook](../onboarding/HOSPITAL_PLAYBOOK.md) | Pilot success → 3-year MSA | Convert rate ≥ 70% |

---

## 3. The 60-second product truth (memorize this)

CyMed is the **only Middle-East-native full-stack hospital operating system.** Single platform, 39 modules across 10 groups. Ships with NPHIES, JoFotara, Hakeem, WHO ICD-11, HyperPay integrations day one. Arabic RTL first-class. Ambient scribe + AI CDS baked in, not add-on. Cross-provider ecosystem (referrals, shared inventory, medical tourism concierge, RMS-aware). Cloud, on-prem, or JO-regional data-residency. 90-day paid pilot with measurable success criteria. Priced per active provider (Clinic/Hospital), per room / per workstation (ancillary), tiered Pilot / Standard / Enterprise.

Aligned to: **JCI · CBAHI · HCAC · CCHI · SFDA.**

Flagship demo prospect: **Specialized Hospital Amman** — 265 beds, 21 ORs, 28 NICU incubators, Cardiac CoE (1st in Jordan, 7th globally).

---

## 4. Ideal customer profile (ICP)

### Fit signals — pursue

- Country: Jordan first, then Saudi Arabia, then UAE
- Size: 50–500 beds (hospital) or 5–50 providers (clinic chain)
- Ownership: private hospitals, hospital groups, private-clinic networks — decision cycle 3–6 months
- Tech stack signal: legacy HIS from 2010–2015 · point solutions for lab/imaging/pharmacy · patient portal is "results-only" or absent · no online booking · no ambient scribe
- Budget signal: capex + opex separate lines · JCI cycle within 24 months · recent RCM friction (DSO > 60d, denial > 8%)
- People signal: strong CMO or CIO who wants to modernize · at least one champion under 45

### Disqualifying signals — walk away

- Board-mandated Epic / Cerner rollout already funded
- No CIO or equivalent (decision-by-committee, no owner)
- Just replaced HIS in the last 24 months
- Public / MoH-owned with no capex authority
- Compliance already in crisis (mid-JCI failure, mid-fraud investigation)
- Wants "free trial" and refuses paid pilot ⇒ not serious buyer

---

## 5. Full sales cycle

| Stage | Owner | Activities | Tools | Duration |
|---|---|---|---|---|
| Prospect | SDR | LinkedIn + cold email · ABM in 3 countries | HubSpot / Apollo | 1–4 weeks |
| Discovery | AE | 30-min Zoom · qualify (BANT + MEDDIC) · demo artifact walkthrough | [QUALIFICATION_SCRIPT.md](QUALIFICATION_SCRIPT.md) · artifact URL | 1 meeting |
| Deep-dive | AE + SE | 60-min on-site · CMO + CIO + CFO in room · local demo · scenarios | [DEMO_LAPTOP_SETUP.md](DEMO_LAPTOP_SETUP.md) · [DEMO_RUNBOOK.md](../demo/DEMO_RUNBOOK.md) | 1–2 meetings, 2–4 weeks |
| Proposal | AE | Pilot MSA + PILOT_AGREEMENT + PRICING + BAA + DPA | [`docs/commercial/`](../commercial/) | 1–2 weeks |
| Contract | AE + legal | Negotiate MSA · get security review passed · BAA + DPA signed | Legal doc pack | 2–6 weeks |
| Pilot kick-off | CS + engineering | Provision environment · seed data · train champions | [HOSPITAL_PLAYBOOK.md](../onboarding/HOSPITAL_PLAYBOOK.md) | 1–2 weeks |
| Pilot execution | CS | Weekly touchpoints · KPI dashboard · case-study data capture | [CASE_STUDY_DRAFT.md](CASE_STUDY_DRAFT.md) framework | 90 days |
| Conversion | AE + CS | Present pilot results · negotiate multi-year MSA | Pilot data + Executive review | 2–4 weeks |
| Expansion | CS | Add editions · add facilities · upsell modules | Executive dashboard + roadmap | Ongoing |

Total cycle: **3–9 months** from cold to closed-won.

---

## 6. Rep-facing content index

| Doc | Purpose | Audience | When to use |
|---|---|---|---|
| [ELEVATOR_PITCH.md](ELEVATOR_PITCH.md) | 30 / 60 / 120s pitches, EN + AR | SDR + AE | Every cold call, every event |
| [ONE_PAGER.md](ONE_PAGER.md) | Printable A4 · problem → solution → CTA | SDR + AE | Attach to intro email · leave-behind at meetings |
| [SALES_DECK_OUTLINE.md](SALES_DECK_OUTLINE.md) | 18-slide narrative + speaker notes | AE | 60-min presentations |
| [QUALIFICATION_SCRIPT.md](QUALIFICATION_SCRIPT.md) | BANT + MEDDIC discovery script | AE | First meeting after cold response |
| [OBJECTIONS_PLAYBOOK.md](OBJECTIONS_PLAYBOOK.md) | 15 objections + concrete responses | AE + SE | Read before every meeting |
| [COMPETITIVE_MATRIX.md](COMPETITIVE_MATRIX.md) | Feature depth + positioning vs 11 competitors | AE + SE | When a specific competitor is named |
| [EMAIL_TEMPLATES.md](EMAIL_TEMPLATES.md) | 8 bilingual templates | SDR + AE | Every cold outreach + post-meeting |
| [CASE_STUDY_DRAFT.md](CASE_STUDY_DRAFT.md) | Illustrative case study + real framework | AE + CS | Post-pilot; illustrative used pre-first-customer |
| [DEMO_LAPTOP_SETUP.md](DEMO_LAPTOP_SETUP.md) | Sales-laptop bring-up in 5 min | SE | Onboarding + on-site demos |
| [CLOUD_DEMO_DEPLOY.md](CLOUD_DEMO_DEPLOY.md) | Always-on public demo devops runbook | Devops | Once, then hand off to sales |
| [DEMO_RUNBOOK.md](../demo/DEMO_RUNBOOK.md) | 30/60 min talk-tracks | AE + SE | Every demo |
| [DEMO_STATUS.md](../demo/DEMO_STATUS.md) | What's real vs stubbed | AE + SE | Answer honest questions |
| [UAT_TEST_PLAN.md](../demo/UAT_TEST_PLAN.md) | 150-point QC checklist | Client + SE | Post-demo handoff |
| [CLIENT_ACCESS.md](../demo/CLIENT_ACCESS.md) | 3 sharing paths (cloud / ngrok / Zoom) | SE | Choosing how client tests |
| [PRICING.md](../commercial/PRICING.md) | Tiers + models + JOD/SAR/AED | AE | Proposal stage |
| [PILOT_AGREEMENT.md](../commercial/PILOT_AGREEMENT.md) | 90-day paid pilot terms | AE + legal | Proposal stage |
| [MSA_TEMPLATE.md](../commercial/MSA_TEMPLATE.md) | Master services agreement | Legal | Contract stage |
| [BAA_TEMPLATE.md](../commercial/BAA_TEMPLATE.md) | HIPAA-style BAA | Legal | Contract stage |
| [DPA_TEMPLATE.md](../commercial/DPA_TEMPLATE.md) | GDPR-style DPA | Legal | Contract stage |
| [SLA.md](../commercial/SLA.md) | 99.9% / 99.95% uptime terms | AE | Enterprise negotiations |
| [HOSPITAL_PLAYBOOK.md](../onboarding/HOSPITAL_PLAYBOOK.md) | 12-week onboarding Gantt | CS | Pilot kick-off |
| [SUPPORT_TIERS.md](../support/SUPPORT_TIERS.md) | SEV1-4 definitions | AE + CS | Enterprise negotiations |

---

## 7. Rep-facing tools

- **CRM:** HubSpot free tier (10 seats, unlimited contacts) — Deal pipeline stages match section 5
- **Meeting scheduler:** Calendly or SavvyCal (personal link per AE)
- **Sales intelligence:** Apollo.io free tier for JO healthcare orgs
- **Demo screen recorder:** Loom or built-in OS recorder
- **Signing:** DocuSign or PandaDoc (has JO-compliant e-signature)
- **KPI dashboard:** Google Sheets template (see below) → later Metabase or Looker
- **Communication:** WhatsApp Business + LinkedIn Sales Navigator (JO market is LinkedIn + WhatsApp heavy)
- **Contract vault:** Google Drive with per-account folders

---

## 8. Commission + comp (ILLUSTRATIVE — final numbers set by leadership)

| Role | Base (annual JOD) | On-target var | Total OTE | Accelerators |
|---|---|---|---|---|
| SDR | 14 K | 6 K (meetings booked) | 20 K | 1.5× above quota |
| AE | 24 K | 24 K (60/40 signed pilot / signed MSA) | 48 K | 2× above 120% quota |
| SE | 22 K | 8 K (win-rate on deals SE touched) | 30 K | Flat |
| CS | 20 K | 8 K (pilot → MSA conversion rate) | 28 K | 1.5× above 80% conversion |

Quotas suggested:
- **SDR:** 6 qualified meetings / month
- **AE Y1:** 6 signed pilots + 2 conversions to MSA (~250 K JOD ARR)
- **AE Y2:** 12 signed pilots + 6 MSAs (~750 K JOD ARR)
- **CS:** 70% pilot-to-MSA conversion

SPIFFs:
- First MSA per country: bonus 10 K JOD to the AE
- Signed hospital > 100 beds: bonus 5 K JOD
- Signed 3-year MSA: 5 K JOD accelerator
- Case study delivered with hospital sign-off: 2 K JOD to whoever owned the account

---

## 9. Jordan year-1 hiring plan

| Month | Hire | Rationale |
|---|---|---|
| M0 | 1 AE (senior, ex-hospital-CIO relationships in JO) | Anchor first deals |
| M2 | 1 SE (background: clinical informatics or pharmacist with 5+ years) | Support technical demos, own pilot success |
| M3 | 1 SDR (Arabic-first, LinkedIn-native) | Feed the pipeline |
| M6 | 1 CS lead (ex-JCI surveyor or ex-hospital-COO) | Own pilot execution |
| M9 | +1 AE (KSA-focus, native Arabic) | Open Saudi market |
| M12 | +1 SE (KSA + UAE) | Support KSA + UAE demos |

Total year-1 cost estimate: ~$450 K USD fully loaded (JO salaries + tools + travel + events).

Ramp targets:
- AE ramps at 6 months to full quota
- SE ramps at 3 months
- SDR ramps at 2 months

---

## 10. KPIs to track

### Weekly (whole team, in one shared dashboard)

- New leads created
- Meetings booked
- Meetings held (show-up rate)
- Opportunities created
- Pipeline value ($ and count) by stage
- Win / loss / stalled per rep

### Monthly (leadership review)

- Bookings (signed contracts $)
- New ARR (annualized recurring revenue)
- Win rate
- Sales-cycle length (days) by stage
- CAC by channel
- Rep quota attainment (%)

### Quarterly (board / investor review)

- ARR run-rate
- Logo count (customers) by tier
- Retention (net revenue retention)
- Gross margin
- Pipeline coverage ratio (pipeline / next-quarter quota — target 3×)
- Attribution: pipeline generation by source

---

## 11. What GOOD looks like at 30 / 60 / 90 days for a new AE

### Day 30
- Completed onboarding: read every doc in `docs/sales/` + `docs/commercial/`
- Delivered demo to internal team, scored ≥ 4/5 on execution
- Passed shadow-call review with sales manager
- 20 first-touch outreaches sent

### Day 60
- 3 opportunities in pipeline (any stage)
- 1 deep-dive demo held (AE + SE)
- Familiar with all objection responses
- Contributed 1 new insight to sales-team weekly

### Day 90
- 1 signed pilot MSA
- 5+ opportunities in pipeline
- Case study data-capture started for the pilot
- Quota attainment on track (100% for Q1)

Miss any of these → coaching intervention; miss 60-day gate → performance improvement plan.

---

## 12. What to escalate to leadership

Immediately (same day):
- Any prospect asks about a competitor lawsuit or fraud allegation
- Any prospect requests uncapped indemnification
- Any prospect requests source-code escrow (may be reasonable — escalate for negotiation strategy)
- Any regulatory scrutiny (SFDA, CBAHI, MoH inquiry)
- Any deal > 500 K JOD ARR
- Any 3-year MSA request
- Any security question you cannot answer

Within 48h:
- Deal at "Contract" stage for > 60 days with no movement
- Loss to a specific competitor twice in 90 days (competitor-specific war-room)
- New feature ask from > 2 prospects (product-marketing loop)

---

## 13. Ethics · compliance · anti-corruption (JO context — read once, remember always)

Jordan is a signatory to the UN Convention Against Corruption. The Jordanian Anti-Corruption Commission (JIACC) enforces bribery laws that apply to healthcare procurement. **Non-negotiable rules:**

- **No cash gifts.** Ever. To anyone. Small business gifts (branded pens, notepads) are OK; anything > JOD 20 in value is not.
- **No fee-splitting with clinicians.** A physician recommending CyMed cannot receive a per-referral fee.
- **No kickbacks disguised as consulting fees.** Advisory board with a real advisor role: OK. Fake advisor with no work: not OK.
- **No gifts to family members** of decision-makers.
- **Full transparency on any hospitality:** meals during business meetings are OK; entertainment outside business hours (sports, concerts, travel) triggers a review — get pre-approval from CFO.
- **No hiring** of a decision-maker's family member within 12 months of a signed deal.
- **Public tender** — never pay a "facilitation fee." Walk away.
- **All contracts** through legal review — never a side-letter.

If asked to do any of the above by a prospect: **decline, log it, escalate to CEO immediately.** We would rather lose the deal than lose the license to operate in JO.

Reference: JO Anti-Corruption Commission Law No. 62 of 2006 (as amended).

---

## 14. Handoffs — SDR → AE → SE → CS

Every handoff carries a handoff note posted in CRM + Slack channel:

### SDR → AE (after meeting booked)

```
Prospect: [name, title, hospital]
Meeting: [date, time, format (in-person / Zoom)]
Source: [LinkedIn / email / referral / event]
Pain hooks landed: [1-3 bullets from the cold call]
Objections raised: [any hesitation from the prospect]
Materials sent: [artifact URL, one-pager, etc]
Suggested opener: [one line to start the meeting warm]
```

### AE → SE (after discovery, deep-dive scheduled)

```
Account: [name, tier from QUALIFICATION rubric]
Champion: [name, title]
Buyer: [name, title]
Meeting: [date, attendees on their side]
Their tech stack: [current HIS, integrations, IT team size]
Their pain: [3 pains ranked]
What they need to see: [3 specific screens or scenarios]
Competitors named: [any]
Deal size estimate: [$ ARR]
Timeline signals: [budget cycle, JCI cycle, etc]
```

### AE → CS (after pilot signed)

```
Account: [name]
MSA signed: [date]
Pilot scope: [modules, facilities, cohort size]
Kick-off: [date]
Executive sponsor (client): [name]
Executive sponsor (Cybercom): [name]
Success criteria: [pre-negotiated KPIs from PILOT_AGREEMENT]
Known risks: [any]
Case-study rights negotiated: [yes / no / partial]
Weekly touchpoint: [day / time]
```

### CS → AE (60 days into pilot for expansion prep)

```
Account: [name]
Pilot status: [green / yellow / red]
KPIs vs targets: [table]
Expansion signals: [who has asked about more editions / facilities]
Blockers: [any]
Renewal / conversion probability: [%]
Recommended next-step: [MSA conversion, upsell modules, add facility]
```

---

## 15. Deal-desk process

Any of the following triggers deal-desk review (48-hour turnaround):

- Discount > 15% off list
- Non-standard payment terms (e.g., 6-month cash-in-arrears)
- Non-standard MSA / BAA / DPA language
- Custom data-residency guarantees
- Custom SLAs (> 99.95%)
- Custom indemnification (uncapped, or > 2× fees paid)
- Multi-year commit with price-lock
- Source-code escrow
- Any deal > 500 K JOD ARR

Deal-desk = CEO + CFO + Head of Sales + Legal. Escalate via `#deal-desk` Slack channel with account name, deal size, and specific ask.

---

## 16. Related documents

- All commercial contracts: [`docs/commercial/`](../commercial/)
- Onboarding + implementation: [`docs/onboarding/`](../onboarding/)
- Client-facing demo material: [`docs/demo/`](../demo/)
- Regulatory reference: [`docs/regulatory/`](../regulatory/)
- Security reference: [`docs/security/`](../security/)

---

## What to do right now (first-week ramp for a new rep)

1. Read this playbook end-to-end (60 min)
2. Read [ELEVATOR_PITCH.md](ELEVATOR_PITCH.md), rehearse 30s version 5× (30 min)
3. Watch the artifact demo — click every module (45 min)
4. Read [OBJECTIONS_PLAYBOOK.md](OBJECTIONS_PLAYBOOK.md) (30 min)
5. Read [COMPETITIVE_MATRIX.md](COMPETITIVE_MATRIX.md) (20 min)
6. Set up laptop with [DEMO_LAPTOP_SETUP.md](DEMO_LAPTOP_SETUP.md) (20 min)
7. Run through the 10 scenarios locally (30 min)
8. Shadow 2 discovery calls (2× 30 min)
9. Roleplay 1 first-meeting with sales manager (60 min)
10. Send first 20 outreaches from [EMAIL_TEMPLATES.md](EMAIL_TEMPLATES.md) template 1 or 2

Total ramp: ~6 hours of study + practice, spread across 3–5 days.

Then go sell.
