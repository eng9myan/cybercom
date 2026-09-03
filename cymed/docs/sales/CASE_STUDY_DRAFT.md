# CyMed — Case Study Drafts

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom sales enablement

---

## Part A — Illustrative case study (mark clearly ILLUSTRATIVE until a real pilot lands)

> **All numbers below are illustrative targets for the demo pitch, NOT actual customer results. Replace with real data after the first paid pilot completes.**

### Specialized Hospital Amman × CyMed — 90-day pilot results (ILLUSTRATIVE)

**Situation**
Specialized Hospital Amman: 265 beds, 21 ORs, 28 NICU incubators, JCI ×6, Cardiac CoE (1st in Jordan, 7th globally for AMI + HF). ~750 consultants, ~1,864 staff. Accepts 11 payers including RMS referrals. Runs a legacy HIS delivered in 2011 with 4 point solutions bolted on for lab, imaging, pharmacy, and RCM.

**Complication**
- Patient portal limited to results only; no native mobile app; no online booking (PR-office contact form)
- Insurance eligibility takes 3–7 minutes per encounter, staffed manually
- Denial rate hovering around 11%; DSO 68 days
- No cross-provider referral tracking; results returned as fax + PDF
- 750 consultants each spend an average of 90 minutes/day on chart notes

**Question**
Can we prove — in 90 days, without disrupting JCI operations — that a unified Middle-East-native platform materially improves patient access, RCM efficiency, and clinician productivity?

**Answer — pilot scope**
- 2 outpatient clinics + 1 pharmacy branch + patient app for early-adopter cohort (5,000 patients)
- Live NPHIES-style adjudication for Aman + MedNet + GlobeMed at pharmacy POS
- Ambient scribe rolled out to 30 volunteer consultants
- Cross-provider referral loop with 2 external radiology partners

**Results at day 90 (ILLUSTRATIVE)**

| Metric | Baseline | Day 90 | Δ |
|---|---|---|---|
| Patient bookings via app | 0/day | 34/day (target 20) | ✓ |
| Insurance eligibility time | 4m 12s | 22s | −90% |
| Pharmacy POS insurance approval | 8m avg | 42s avg | −91% |
| Denial rate (pilot claims cohort) | 11.2% | 4.1% | −7.1 pp |
| DSO (pilot cohort) | 68d | 41d | −27d |
| Ambient scribe: minutes saved/consultant/day | 0 | 74 | +74 min |
| Cross-provider referral loop closure < 48h | 41% | 88% | +47 pp |
| Patient portal MAU (pilot cohort) | ~800 | 3,940 | +3,140 |
| Patient NPS (post-visit) | 42 | 61 | +19 |
| Clinician satisfaction (single-item) | 3.1/5 | 4.2/5 | +1.1 |

**Quotes (ILLUSTRATIVE — replace with real quotes on real customer)**

> "The 90 minutes I used to spend on notes each evening — I now spend them with my family. The scribe wrote what I said. I signed. Done."
> — *Dr. [Cardiology consultant], Specialized Hospital Amman (ILLUSTRATIVE)*

> "For the first time our denial predictor catches modifier errors BEFORE we submit. Our RCM team stopped writing the same appeal letter three times a week."
> — *[Head of RCM], Specialized Hospital Amman (ILLUSTRATIVE)*

> "We chose CyMed over a global vendor because the ambient scribe already speaks Arabic and understands our workflow. And because the pilot terms were fair — pass or fail on measurable KPIs, and we own the data."
> — *[CIO], Specialized Hospital Amman (ILLUSTRATIVE)*

**Decision after pilot (ILLUSTRATIVE)**
Converted to Standard tier, 3-year MSA, phased rollout across all 8 sub-facilities over 12 months.

---

## Part B — Real case-study framework

Use this after any pilot converts. Do NOT publish anything with real customer names or data until every section below is complete AND legal + customer sign-off is on file.

### Data collection checklist — during the pilot

Weekly during pilot (RCM analyst owns):
- [ ] Bill count + gross charges + net collected (pilot cohort only)
- [ ] Denial rate: total denials / total submissions
- [ ] First-pass yield: claims paid without appeal / total claims
- [ ] DSO: (AR / net credit sales) × days
- [ ] AR aging by bucket (0–30, 31–60, 61–90, > 90)
- [ ] Appeal recovery: JOD recovered / total appealed

Weekly during pilot (clinical ops owns):
- [ ] Patient throughput per clinic / per specialty
- [ ] Door-to-doc time (ED cohort if included)
- [ ] No-show rate for booking cohort
- [ ] Ambient scribe usage: sessions per consultant per day
- [ ] Ambient scribe minutes saved (self-reported + calculated from note-length delta)

Weekly during pilot (patient experience owns):
- [ ] Patient app MAU / DAU
- [ ] Bookings via app / total bookings
- [ ] E-Rx refills / total refills
- [ ] NPS single-item score (post-visit push)
- [ ] Complaints logged (compare to baseline period)

End-of-pilot (analytics owns):
- [ ] Full baseline vs day-90 delta table
- [ ] Statistical significance where n permits (chi-square for rates, t-test for continuous)
- [ ] Confounder log — anything else that changed during the period that could explain results

### Interview scripts

**Physician (30 min):**
1. Walk me through a typical clinic day before CyMed. Now walk me through today.
2. What is the single thing that changed most for you?
3. What did you fear before we started? Did it happen?
4. What would you tell a peer at another hospital who is deciding?
5. Anything you would change or extend?

**Nurse (30 min):**
1. How has the e-MAR affected your medication rounds?
2. Any near-miss or catch you attribute to the CDSS?
3. How does the shift handover feel compared to before?
4. What is still painful?

**RCM staff (30 min):**
1. Walk me through claim submission before vs now.
2. Which denial code hurt you most historically? Has it moved?
3. How is the denial predictor changing your work?
4. What is the biggest surprise?

**CFO (45 min):**
1. What financial KPI moved most that you did not expect?
2. How does the cost of CyMed compare to the value you have measured?
3. What would you need to see to expand across all facilities?
4. What is the board's view?

**CEO (60 min):**
1. What did this pilot prove or disprove for your strategic thesis?
2. How does CyMed change your competitive position in the market?
3. If you were a peer CEO, how would you make this decision?
4. What does regional expansion look like?

### Approval and consent workflow

1. **Publish-rights clause in pilot MSA** — pre-negotiated. Customer approves specific outputs, not the case study concept. See `docs/commercial/PILOT_AGREEMENT.md`.
2. **Data-privacy scrub** — remove all patient identifiers, aggregate at cohort level, JO PDPL alignment check.
3. **Customer draft review** — 10 business days for comments. Two rounds max.
4. **Legal sign-off** — both sides, before any publication.
5. **Rights of retraction** — customer can withdraw quote at any time within 12 months of publication.
6. **Attribution policy** — spokesperson name + title + hospital only if explicitly opted-in per quote.

### Case study template — 6 placeholder sections

```
# [Hospital name] × CyMed — [Edition] rollout results

## At a glance
- Country, city, size, accreditation
- Editions deployed, timeline
- Headline result (one number + one quote)

## The situation
- What the customer was doing before
- Why they invested in change now
- Selection process, alternatives considered

## The pilot / rollout
- Scope, timeline, teams involved
- Governance model (steering committee, meetings)
- Technical footprint (cloud / on-prem / hybrid)

## Results
- Table: metric | baseline | day 90 | day 180 | day 365
- Statistical notes where relevant
- Qualitative outcomes (culture, adoption, retention)

## In their words
- 2-3 short quotes with named attribution

## What is next
- Expansion plans
- New workflows planned
- Regional or new-edition adoption
```

### Design guide for the final PDF

- **Format:** A4 portrait, 4–6 pages, 6–8 MB
- **Typography:** IBM Plex Sans (same family as the demo — brand-consistent). Body 10pt, headings 14/16/22pt.
- **Palette:** Cybercom gradient #0062CC → #00D4AA reserved for the cover only. Body text on cream (#FAF9F5) or pure white. Numbers in IBM Plex Mono for tabular clarity.
- **Imagery:** photos of the hospital exterior + one photo of the actual system in use if the customer permits. NO stock imagery.
- **Data viz:** two charts max — one for RCM outcomes, one for adoption. No 3D, no gradients on bars, no pie charts.
- **Cover:** hospital name + tagline + one big number + result summary in 12 words.
- **Back:** contact info, related case studies, a 60-word Cybercom boilerplate.

### Distribution

- Website: `cymed.io/case-studies/[hospital-slug]`
- LinkedIn: cover image + 4-slide carousel + 800-char intro from the AE who ran the deal
- Sales collateral: bundled in Tier-2 (post-discovery) email templates — see `docs/sales/EMAIL_TEMPLATES.md`
- Conference: 1-page handout version, same numbers

---

## What to publish now (before real case study lands)

Use the Specialized Hospital demo as a *concrete-scenario* pitch:
- Never claim it as a real customer outcome
- Frame it as "here is exactly what a 90-day pilot at Specialized Hospital Amman would measure and target"
- Point at the demo artifact + UAT checklist as evidence the platform is real and audit-ready
