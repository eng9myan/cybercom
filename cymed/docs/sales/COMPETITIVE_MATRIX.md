# CyMed Competitive Matrix

| Field | Value |
|---|---|
| Version | 1.0 |
| Date | 2026-08-26 |
| Owner | Cybercom sales enablement |
| Audience | CyMed sales reps, pre-meeting brief |
| Scope | Middle East, Jordan-first, KSA & UAE next |

Related docs: [Elevator pitch](./ELEVATOR_PITCH.md) · [Email templates](./EMAIL_TEMPLATES.md) · [Pilot terms](./PILOT_TERMS.md) · [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69) · [Cloud demo](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656)

---

## How to read this document

- Table 1 tells you what CyMed does that the other side does not. Point at it.
- Table 2 tells you how each competitor pitches, where they crack in the ME, and where you exit if the deal is not ours.
- The two scenario sections are the muscle memory for the objection you will actually hear.
- Numbers are from the CyMed sales pack. Any figure marked *(illustrative)* is a working example, not a quote.

---

## Table 1 — Feature depth matrix

Legend: `V` full native · `P` partial (limited scope or workflow gaps) · `A` add-on (extra license, third-party module, or SI build) · `X` not available.

| # | Capability | CyMed | Epic | Oracle Health (Cerner) | InterSystems TrakCare | InfoMed (JO) | DXware (JO) | Bayanat Al-Oula (KSA) | Generic HIS |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EMR core | V | V | V | V | V | P | V | P |
| 2 | CPOE | V | V | V | V | P | P | V | P |
| 3 | ADT | V | V | V | V | V | V | V | V |
| 4 | Nursing eMAR | V | V | V | V | P | P | P | P |
| 5 | Lab / LIS | V | A | A | V | A | A | P | A |
| 6 | Radiology RIS + PACS | V | A | A | P | A | A | A | A |
| 7 | Pharmacy | V | V | V | V | P | P | V | P |
| 8 | Blood bank | V | A | A | P | X | X | A | A |
| 9 | CDSS | V | V | V | P | X | X | P | X |
| 10 | Ambient scribe | V | A | A | X | X | X | X | X |
| 11 | Patient portal (web) | V | V | V | V | P | P | P | P |
| 12 | Patient app (native mobile) | V | V | V | P | X | X | P | X |
| 13 | Telemedicine | V | A | A | P | A | A | A | A |
| 14 | NPHIES connector (KSA) | V | A | A | A | A | A | V | X |
| 15 | JoFotara connector (JO e-invoice) | V | X | X | X | P | P | X | X |
| 16 | Hakeem push (JO national record) | V | X | X | X | P | X | X | X |
| 17 | Arabic RTL first-class | V | P | P | P | V | V | V | P |
| 18 | Cross-provider referral | V | P | P | P | X | X | X | X |
| 19 | Medical tourism concierge | V | X | X | X | X | X | X | X |
| 20 | Loyalty / membership | V | X | X | X | X | X | X | X |

### Depth score summary

| Vendor | V | P | A | X | Practical read |
|---|---|---|---|---|---|
| CyMed | 20 | 0 | 0 | 0 | One platform, 39 modules, ME-native. |
| Epic | 11 | 3 | 6 | 0 | Deep clinical core, integration-tax on ancillaries and ME. |
| Oracle Health (Cerner) | 10 | 3 | 6 | 1 | Same story as Epic, weaker on Hakeem/JoFotara. |
| InterSystems TrakCare | 8 | 8 | 2 | 2 | Broadest single-suite competitor, thin on scribe/loyalty/tourism. |
| InfoMed (JO) | 5 | 8 | 4 | 3 | Local footprint, no AI, no ecosystem. |
| DXware (JO) | 3 | 8 | 3 | 6 | Small clinics, weak certification story. |
| Bayanat Al-Oula (KSA) | 6 | 5 | 4 | 5 | NPHIES-native like us, no cross-border story. |
| Generic HIS | 2 | 8 | 5 | 5 | Reference row for "the incumbent" objection. |

---

## Table 2 — Positioning against each competitor

| Competitor | Their pitch | Their weakness in ME market | CyMed's angle | When to walk away |
|---|---|---|---|---|
| **Epic** | "Global gold standard, used by top academic centers." | 24–36 month deploy; USD-priced; JoFotara/Hakeem not built; Arabic is right-to-left retrofit; ancillaries via partners. | One platform, ME-native, 90-day pilot, per-provider pricing in JOD/SAR/AED. | Ministry mandates Epic by name, or the buyer already signed an Epic MSA. Do not fight the paper. |
| **Oracle Health (Cerner)** | "Enterprise EHR with the Oracle cloud stack." | Post-acquisition roadmap uncertainty; NPHIES/JoFotara built by SI, not vendor; heavy on-prem legacy. | Vendor-owned local integrations, cloud + on-prem + JO-regional residency, ambient scribe in the base license. | Group is already mid-Cerner-to-Oracle migration and has a signed roadmap. |
| **InterSystems TrakCare** | "Single suite, strong in ME, Cache/IRIS backbone." | No native ambient scribe; loyalty/tourism absent; cross-provider referral is a custom project; Arabic uneven across screens. | 39 modules vs their 20-ish; AI CDS + scribe baked in; cross-provider ecosystem is real, not a slide. | Buyer wants InterSystems-certified data platform for research (IRIS) and will not compromise. |
| **InfoMed (JO)** | "We are the Jordanian standard, we know your ministry." | No CDSS, no ambient scribe, weak mobile, no cross-provider, thin JCI evidence. | Same local knowledge (we are Cybercom, JO-based) plus AI, mobile, ecosystem, JCI/HCAC alignment. | Buyer's IT director came from InfoMed and will block on relationship, not features. |
| **DXware (JO)** | "Affordable, fast, familiar." | Small-clinic ceiling; certification gaps for JCI/HCAC; no NPHIES; no ecosystem. | Same time-to-live via 90-day pilot, at a hospital-grade platform they can scale into. | Prospect is a single-doctor clinic under 5 rooms and price is the only axis — send them to our Clinic Pilot tier or bow out. |
| **Bayanat Al-Oula (KSA)** | "NPHIES-native, CBAHI-aware, Saudi-first." | KSA-only; no JO/UAE roadmap; no Hakeem; no medical tourism; ambient scribe missing. | We are NPHIES-native too, plus JoFotara + Hakeem + CCHI, so a KSA group with a JO/UAE branch gets one platform. | A pure-KSA operator with zero regional expansion appetite. |
| **Alpha (KSA)** | "SFDA-registered pharmacy and HIS bundle." | Pharmacy-forward, thin on ICU/OR/NICU depth; no AI CDS. | Full-stack acute + ancillary + AI in one contract. | Standalone pharmacy chain with no hospital scope. |
| **Medware (LB) / Perfect Health** | "Regional player, price-competitive." | Fragmented modules; JCI evidence weak; no ecosystem or patient app. | Concrete certifications alignment + patient-app delegated pay + tourism concierge. | Buyer is buying by lowest sticker price and refuses to price a pilot. |
| **Allscripts / Altera** | "US-scale ambulatory + acute." | ME footprint is thin; no local e-invoice or national record connectors. | ME-native connectors, JOD/SAR/AED billing, Arabic-first UI. | Group is a US chain opening a ME arm and IT is centralised in the US. |
| **athenahealth** | "Cloud-native, revenue cycle strength." | US-centric RCM; no NPHIES/JoFotara; no on-prem option (blocker for KSA regulated data). | Cloud + on-prem + JO-regional residency; RCM tied to NPHIES/JoFotara/CCHI. | Prospect explicitly wants US-billing SaaS and is not regulated locally. |
| **Cliniko / Zoho Health / DrChrono** | "Cheap, month-to-month, easy signup." | Single-clinic scope; no ICU/OR/lab/imaging depth; no Arabic-first; no ME connectors. | Our Clinic edition matches their setup speed and price band, then scales when they open a second site. | 1–2 provider clinic with no growth plan and no compliance need. |

---

## When we lose to X

Three lose scenarios you have to know before the meeting. Each carries the lesson so the next rep does not repeat the mistake.

### 1. Lose to Epic — the "board mandate" loss
- **What happened.** Group's board benchmarks against a Gulf academic medical centre already on Epic. The CMO frames Epic as the safe career choice.
- **Signals during the cycle.** Buyer asks for KLAS scores. RFP language is Epic-shaped ("integrated care everywhere", "MyChart"). IT team requests references only from US/EU flagship sites.
- **Lesson.** We are not Epic. Do not try to be. Fight on ME-native (NPHIES, JoFotara, Hakeem, Arabic RTL) and time-to-live (90 days vs 24 months). If they cannot hear that story, they were never our deal.

### 2. Lose to InfoMed — the "incumbent relationship" loss
- **What happened.** InfoMed already runs the hospital's registration and billing. Ops team fears a re-implementation. IT director trained on InfoMed.
- **Signals during the cycle.** Buyer keeps asking "can you talk to InfoMed data?" Meeting attendance drops after the demo. Legal never engages.
- **Lesson.** Do not try to displace InfoMed head-on. Land the ancillary they do not have (imaging, ICU, ambient scribe, patient app) as a 90-day pilot. Let module wins pull the rest.

### 3. Lose to Bayanat Al-Oula (KSA only) — the "we already speak NPHIES" loss
- **What happened.** Riyadh group already integrated Bayanat with NPHIES; the CCHI submission story is proven; migration risk feels too high.
- **Signals during the cycle.** Buyer asks about "compatibility" not "replacement". Payer team is happy. Cost of switching is priced in the RFP.
- **Lesson.** Position CyMed as the *cross-border* platform for their JO/UAE expansion, not as a KSA rip-and-replace. Land a branch. Let clinical differentiation (AI CDS, ambient scribe) do the second-year expansion.

---

## When they will lose to us

Four scenarios where CyMed wins by design. Steer the conversation toward these.

### 1. Multi-site multi-country group (JO + KSA + UAE)
- Competitors force one contract per country (or one implementation per country) because their local connectors are per-vendor SI work.
- CyMed ships NPHIES + JoFotara + Hakeem + CCHI + SFDA in the base license and prices per-active-provider across countries.
- Ask: *"How long does it take Cerner to add JoFotara to your Amman branch?"* Answer today: an SI project. Ours: a config flag.

### 2. Medical tourism operator (JO or KSA)
- No competitor ships a medical tourism concierge module. Not Epic, not TrakCare, not InfoMed.
- CyMed ties the concierge module to the patient app with delegated pay (family abroad settling the JO patient's bill) and cross-provider referral.
- Ask: *"When a Sudanese family sends a patient to Amman and pays from Riyadh, who sends the discharge summary to the referring GP and reconciles the invoice?"* Silence is our close.

### 3. Ambient-scribe-driven productivity story
- Physician burnout is a boardroom topic. Competitors ship scribe as an add-on (Nuance/Nabla partnership fees, extra USD per provider per month).
- CyMed ships ambient scribe in the base per-active-provider price. *(Illustrative: a 40-provider clinic pays zero incremental scribe fees vs ~USD 200/provider/month elsewhere = ~USD 96,000/year saved.)*
- Ask: *"What is the all-in per-provider cost with scribe included?"* Force the competitor to quote the add-on.

### 4. Rural / offline-first / regional-residency deployment
- MRFF alignment: offline-first rural. KSA and JO both have regulated data residency for hospitals outside tier-1 cities.
- CyMed runs cloud, on-prem, and JO-regional. Epic and athena are cloud-mainly; TrakCare and Cerner on-prem is heavy. Bayanat is KSA-only cloud.
- Ask: *"If we open a 30-bed site in Aqaba or Tabuk with intermittent connectivity, does your platform stay clinical without WAN?"* Ours does.

---

## Fast reference card

| Fact | Number |
|---|---|
| Modules | 39 across 10 groups |
| Editions | Clinic, Hospital, Lab, Imaging, Pharmacy + Ecosystem add-on |
| Pilot | 90-day paid, with success criteria (not a free trial) |
| Certifications aligned | JCI, CBAHI, HCAC, CCHI, SFDA |
| Local connectors | NPHIES (KSA), JoFotara (JO), Hakeem (JO), HyperPay, WHO ICD-11 |
| Pricing axes | per-active-provider (Clinic/Hospital), per-room / per-workstation (ancillary) |
| Tiers | Pilot / Standard / Enterprise |
| Deployment | Cloud, on-prem, JO-regional data residency |
| Paperwork ready | MSA, BAA, DPA |
| Flagship prospect | Specialized Hospital Amman |

---

## One-line answers to the objection you will actually hear

| They say | You say |
|---|---|
| "Are you Epic?" | "No. Epic is a 24-month deploy priced in USD. We are 90 days, priced in JOD/SAR/AED, with NPHIES, JoFotara, Hakeem, and Arabic RTL in the box." |
| "InfoMed already does this." | "InfoMed does registration and billing. We ship imaging, ICU, ambient scribe, patient app, and cross-provider referral. Start with what they do not have." |
| "Ambient scribe is a nice-to-have." | "Physicians close their day 42 minutes earlier *(illustrative)*. That is one more clinic hour per provider per day. Multiply by your provider count." |
| "We need NPHIES and CCHI." | "Built in. Same for JoFotara, Hakeem, HyperPay, ICD-11. No SI, no partner license, no separate contract." |
| "Give us a free trial." | "We do a 90-day paid pilot with signed success criteria. You get money-back if we miss them. That is a better deal than free — it means we are accountable." |
| "Your company is smaller than Epic." | "Correct. That is why your JoFotara connector is a config flag and Epic's is a project." |
