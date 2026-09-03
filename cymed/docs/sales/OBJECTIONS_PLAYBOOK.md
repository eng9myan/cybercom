# CyMed Objections Playbook

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom sales enablement
**Audience:** CyMed field sales — read this in the car on the way to the meeting.

---

## How to use this playbook

- Every objection below follows the same shape: **Why they say it → Response → Proof → Redirect question.**
- The Proof column is what closes the objection. Have the artifact open on your phone or tablet before you walk in.
- Never bulldoze. Acknowledge the concern in one sentence, deliver the response, then hand the conversation back with the redirect question.
- Middle-East selling is credential-first. Lead with certifications, references, and named people — never with features.

### Standing proof set (memorize these numbers)

| Asset | Value | Where |
|---|---|---|
| Cloud demo | Live sandbox with seeded JO clinic | https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656 |
| UAT checklist | 90-day pilot acceptance criteria | https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69 |
| Module count | 39 modules across 10 clinical groups | Product one-pager |
| Local integrations shipped | NPHIES, JoFotara, Hakeem, HyperPay, WHO ICD-11 | Integration matrix |
| Certification alignment | JCI, CBAHI, HCAC, CCHI, SFDA | Compliance dossier |
| Pilot commercial model | 90-day **paid** pilot with written success criteria | MSA + SOW template |

---

## Objection 1: "We already have InfoMed / DXware / X — we can't switch."

**Why they say it:** Real fear of migration cost, data loss, and clinician retraining. Also political — someone signed the current contract.

**Response:** We do not ask you to rip and replace on day one. CyMed runs alongside your incumbent through HL7 v2 and FHIR R4 feeds; you pick one department — usually ED or lab — for the 90-day pilot and measure. If the numbers do not beat your baseline, you keep the incumbent and we walk away.

**Proof:**
- [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69) — success criteria are agreed in writing before pilot start.
- Integration matrix: HL7 ADT/ORM/ORU, FHIR R4 (Patient, Encounter, Observation, MedicationRequest), DICOM C-STORE/C-FIND for PACS side-by-side operation.

**Redirect question:** *"Which single department is costing you the most in rework or write-offs today? That is where we should run the 90 days."*

---

## Objection 2: "Our data can't leave Jordan."

**Why they say it:** Data-sovereignty requirement from MoH, or hospital board policy on PHI residency. Sometimes NPHIES / CCHI wording is mis-read as banning cloud.

**Response:** CyMed is deployed in three modes: cloud, on-prem, or JO-regional data residency in-country. Patient identifiable data stays inside Jordan for JO tenants; only aggregated, de-identified telemetry can optionally leave for benchmarking, and you switch that off with one flag.

**Proof:**
- Data-residency architecture diagram (see [/docs/architecture/DATA_RESIDENCY.md](../architecture/DATA_RESIDENCY.md)).
- DPA template with Jordan Personal Data Protection Law (Law No. 24 of 2023) clauses.
- On-prem deployment reference build: Kubernetes on customer hardware, air-gapped upgrade channel.

**Redirect question:** *"Is your preference in-country cloud or on-prem in your own data center? Both are supported — the answer just changes the SOW."*

---

## Objection 3: "You're new — where's your reference customer?"

**Why they say it:** Legitimate risk aversion in a life-safety product. They need to defend the choice to their board.

**Response:** CyMed is new to market, and we are transparent about that — which is exactly why the commercial model is a **paid 90-day pilot with written success criteria**, not a multi-year lock-in. Specialized Hospital Amman is our flagship reference in negotiation; being an early named partner earns preferred pricing and a permanent seat on the clinical advisory board.

**Proof:**
- Cybercom engineering track record (parent platform: Cycom ERP, CyED school system — both live).
- [Pilot SOW template](../commercial/PILOT_SOW.md) — success criteria, exit clause, IP escrow.
- Clinical advisory board charter — reference customers co-own the roadmap.

**Redirect question:** *"Would you rather be the reference customer for the region — with the leverage that gives you — or the tenth site after the flagship is signed?"*

---

## Objection 4: "Epic / Cerner is the safe choice, no one gets fired for Epic."

**Why they say it:** Career risk. Epic has brand safety. The buyer is protecting themselves, not evaluating the product.

**Response:** Epic and Oracle Health are excellent products built for the US market. They are also 18-to-36-month implementations at eight-figure total cost with Arabic and NPHIES handled by third parties. CyMed goes live in 90 days at a fraction of the cost, with NPHIES, JoFotara, Hakeem, CCHI and SFDA already in the core — not bolted on by a consulting partner charging by the hour.

**Proof:**

| Dimension | Epic / Cerner (typical ME deployment) | CyMed |
|---|---|---|
| Implementation time | 18–36 months *(illustrative — public deals)* | 90 days to first go-live |
| Arabic / RTL | Third-party layer | Native, day one |
| NPHIES / JoFotara | Integration project | In core |
| Modules included | Buy per module | 39 modules, one platform |
| Total cost of ownership | 8-figure USD *(illustrative)* | Per-provider / per-room, tiered |

**Redirect question:** *"If NPHIES and JoFotara are already handled and the go-live is 90 days, what is left of the 'safe choice' argument beyond the logo?"*

---

## Objection 5: "Our clinicians won't adopt yet another system."

**Why they say it:** They have scars from a prior EMR rollout that clinicians resisted. Real pain, not an excuse.

**Response:** Clinician resistance almost always comes from click-count and documentation burden. CyMed ships the **ambient scribe in the core product**, not as a paid add-on — the physician talks to the patient in Arabic or English, the note writes itself, and the ICD-11 codes attach automatically. In pilot benchmarks we target a documentation-time reduction against the incumbent baseline, measured in the UAT.

**Proof:**
- Ambient scribe demo in the [cloud sandbox](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656) — record 60 seconds of consultation and read the note it produces.
- [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69) — one of the success criteria is measured clinician-time-per-encounter.
- Clinician change-management plan in the SOW: 2 weeks shadow, 2 weeks parallel, 2 weeks cutover.

**Redirect question:** *"Would you like to run a 30-minute ambient-scribe session with one of your consultants next week, in a real consulting room?"*

---

## Objection 6: "We're mid-JCI cycle — we can't disrupt now."

**Why they say it:** JCI survey is imminent and the CQO does not want a new variable.

**Response:** CyMed is **JCI-aligned by design** — the quality module maps IPSGs, medication reconciliation, and incident reporting to the JCI 7th-edition standards. A pilot during a JCI cycle typically strengthens the survey, because JCI surveyors specifically ask for evidence of continuous improvement. We time the go-live to your survey window, not against it.

**Proof:**
- JCI IPSG-to-module mapping in [/docs/compliance/JCI_MAPPING.md](../compliance/JCI_MAPPING.md).
- Quality module: incident reporting, root-cause workflows, mortality & morbidity register.
- HCAC alignment for JO, CBAHI alignment for KSA — same underlying quality engine.

**Redirect question:** *"When is your next JCI survey window, and would timing the pilot after the survey — or specifically to demonstrate improvement in the next cycle — work better for the CQO?"*

---

## Objection 7: "Prove your AI CDS is safe."

**Why they say it:** They read a headline about a hallucinating AI in medicine and are now (correctly) cautious.

**Response:** The CDS module never auto-prescribes and never auto-diagnoses. It surfaces suggestions — drug-drug interactions, dose-by-weight, differential prompts — and every suggestion is logged with the source evidence and a required clinician accept/reject action. Model outputs are grounded in a curated knowledge base (WHO ICD-11, national formularies), not a general-purpose LLM. And every AI action is auditable to the individual clinician who approved it.

**Proof:**
- CDS safety architecture: [/docs/safety/CDS_SAFETY.md](../safety/CDS_SAFETY.md) — human-in-the-loop, evidence links, audit log.
- WHO ICD-11 integration is live (OAuth2 client_credentials, verified) — codes and definitions come from the WHO API, not a model guess.
- Model output labeling: every AI-suggested field is visually distinct in the chart and requires clinician confirmation to persist.

**Redirect question:** *"Would your CMO like a 45-minute technical walkthrough of the CDS safety model with our clinical lead before the pilot starts?"*

---

## Objection 8: "What about our current PACS / lab / pharmacy investment?"

**Why they say it:** Sunk cost. They just paid for equipment or a system, and cannot justify replacing it.

**Response:** You do not replace it. CyMed speaks DICOM to your PACS, HL7 v2 ORU to your LIS, and standard prescription messaging to your pharmacy dispensers. The Imaging, Lab, and Pharmacy editions of CyMed are optional — the Clinic and Hospital editions integrate with what you already own.

**Proof:**

| Existing system | Integration protocol | CyMed effort |
|---|---|---|
| PACS (Agfa, Sectra, GE, Philips) | DICOM C-STORE, C-FIND, WADO-RS | Configure in pilot |
| LIS (Roche, Sysmex, in-house) | HL7 v2 ORM / ORU | Configure in pilot |
| Pharmacy dispenser | HL7 v2 RDE / NCPDP SCRIPT | Configure in pilot |
| Radiology worklist | DICOM Modality Worklist | Configure in pilot |

**Redirect question:** *"Which of these systems is the one you are happiest with — because that becomes the integration we lead with, and the rest follow the same pattern."*

---

## Objection 9: "The Arabic support in Epic is fine — why do we need Arabic-first?"

**Why they say it:** They have seen an Arabic-labeled Epic screen and think the problem is solved.

**Response:** Labels being translated is not Arabic-first. Arabic-first means: right-to-left layout that mirrors correctly, Arabic-Indic numerals in vitals and dosing where the clinician expects them, Hijri and Gregorian calendar side-by-side, Arabic clinical documentation search that handles diacritics and script forms, and — critically — ambient scribe that transcribes Arabic consultations. Nurses charting in a translated LTR EMR make errors; that is a JCI patient-safety finding, not a preference.

**Proof:**
- Live sandbox: [switch language](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656) top-right and observe the layout mirror, not just the labels.
- Arabic ambient-scribe demo — dictate a case in Arabic, read the structured note.
- Hijri date support in appointment and medication timelines.

**Redirect question:** *"Would your head nurse spend 20 minutes with the Arabic charting flow next week and give us her honest comparison?"*

---

## Objection 10: "How do we know you'll still be in business in 5 years?"

**Why they say it:** Vendor viability risk. Fair for a mission-critical system.

**Response:** Three protections. First, **source-code escrow** — if Cybercom ceases operations, you receive the source and can self-host indefinitely. Second, CyMed is built on open standards (FHIR, HL7, DICOM) — your data is portable to any FHIR-compliant successor system. Third, Cybercom is a multi-product engineering company — CyMed is one of several products including Cycom ERP and CyED — not a single-bet startup.

**Proof:**
- IP escrow clause in [MSA template](../commercial/MSA_TEMPLATE.md) — triggered by insolvency or 90-day service failure.
- FHIR R4 export tooling — full patient record export in standard FHIR bundles.
- Cybercom product portfolio: Cycom ERP (live), CyED (live), CyMed.

**Redirect question:** *"Would having the source-code escrow triggered on 90-day service failure — not just insolvency — reassure your board?"*

---

## Objection 11: "Price is too high compared to X."

**Why they say it:** They are comparing sticker prices, not TCO. Or they have a real budget ceiling.

**Response:** Ask what "X" includes. CyMed's per-active-provider or per-room price includes the ambient scribe, CDS, patient app, NPHIES/JoFotara connectors, and 39 modules. Competitors quote a base HIS and then add: scribe (per-provider add-on), CDS (per-provider add-on), patient portal (per-tenant add-on), and each local integration as a separate project. Run the TCO over 3 years including these line items and CyMed is materially lower.

**Proof:**

| Line item | Competitor typical | CyMed |
|---|---|---|
| Base HIS / EMR | Included | Included |
| Ambient scribe | Add-on per provider *(illustrative)* | Included |
| Clinical decision support | Add-on per provider *(illustrative)* | Included |
| Patient app | Add-on per tenant *(illustrative)* | Included |
| NPHIES / JoFotara connector | Integration project *(illustrative)* | Included |
| Medical-tourism concierge | Not offered | Included in Ecosystem add-on |

- 3-year TCO worksheet: [/docs/commercial/TCO_WORKSHEET.md](../commercial/TCO_WORKSHEET.md).

**Redirect question:** *"Can you share the competitor quote with names removed? We will map it line-by-line so you can compare apples to apples in front of your CFO."*

---

## Objection 12: "Our IT team is 4 people — we can't implement this."

**Why they say it:** Real capacity constraint. Prior implementations have burned them.

**Response:** The pilot is delivered by the Cybercom implementation team, not by yours. Your 4 people are needed for two things: identifying clinical champions and approving integrations to your existing systems. On the cloud edition the entire infrastructure — servers, backups, patching, security — is Cybercom's responsibility. On-prem is available if you require it, and comes with a managed-services option.

**Proof:**
- SOW staffing model in [pilot SOW template](../commercial/PILOT_SOW.md): Cybercom PM, solutions architect, clinical informaticist, 2 engineers.
- Managed-services SLA: 24×7 for P1, 99.9% uptime target on cloud edition.
- Customer-side effort estimate: 0.5 FTE clinical champion + 0.25 FTE IT liaison during pilot.

**Redirect question:** *"If your IT team's effort during the pilot is capped at 0.25 FTE liaison, does the capacity concern still block us?"*

---

## Objection 13: "MoH won't allow a new HIS without approval."

**Why they say it:** Regulatory reality in JO, KSA, and UAE. Sometimes accurate, sometimes an internal excuse.

**Response:** CyMed is designed to be presented for MoH review. In Jordan we align to MoH e-health guidelines and the Hakeem national record; in KSA to CBAHI and NPHIES; in UAE to the DoH and MoHAP requirements. We supply the compliance dossier — data flows, encryption, hosting, DPA — as a submission-ready package. If the MoH conversation has not started, we help you frame it; if it has, we participate.

**Proof:**
- Compliance dossier template: [/docs/compliance/MOH_SUBMISSION.md](../compliance/MOH_SUBMISSION.md).
- Hakeem, NPHIES, JoFotara integrations are already live in the platform.
- Cybercom has engineering staff available to attend MoH meetings alongside you.

**Redirect question:** *"Would it help if we prepared the MoH submission package as the first pilot deliverable, before any clinical go-live?"*

---

## Objection 14: "Can we start with just the patient app and see how it goes?"

**Why they say it:** They want a low-commitment entry point. Sometimes a genuine wedge, sometimes a way to defer the real decision.

**Response:** The patient app is available standalone, and it is a legitimate wedge — especially the delegated-pay feature for family-abroad settling a JO patient's bill, which no competitor offers. But be honest with yourself about the goal: the app alone does not fix ED throughput, RCM leakage, or JCI evidence. If the objective is patient experience, start with the app; if the objective is operational or financial, start with ED, RCM, or clinical documentation instead.

**Proof:**
- Patient app + delegated-pay demo in the [cloud sandbox](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656).
- HyperPay integration is live — payments in JOD, SAR, AED, USD.
- Patient-app-only pricing tier is documented in the commercial pack.

**Redirect question:** *"What is the number-one board-level pain — patient experience, throughput, or margin? The answer picks the wedge."*

---

## Objection 15: "We want a free trial before we commit to a paid pilot."

**Why they say it:** Procurement reflex. Free trials feel safer.

**Response:** Free trials fail in healthcare because no one is accountable for outcomes. The 90-day **paid** pilot is built around this failure mode: written success criteria, a joint steering committee, and a **money-back clause if the success criteria are not met**. It costs the same as a free trial if we don't perform — and it forces both sides to invest properly, which is why pilots that convert to production do so at a much higher rate than free trials.

**Proof:**
- [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69) — the exact success criteria, signed at pilot kickoff.
- Money-back clause language in [pilot SOW template](../commercial/PILOT_SOW.md).
- Free sandbox access is available today — the [cloud demo URL](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656) — for evaluation before the paid pilot begins.

**Redirect question:** *"If the pilot is money-back-guaranteed against the success criteria you set, what is left of the risk that a free trial would remove?"*

---

## Appendix A: Objection triage — which one are you really hearing?

| Surface objection | Often actually means | Actually address by |
|---|---|---|
| "Too expensive" | "I can't defend this to my CFO" | TCO worksheet + line-item comparison |
| "We already have X" | "I signed the X contract" | Side-by-side pilot, not replacement |
| "Not now" | "I don't trust you yet" | Reference customer + escrow + paid pilot |
| "Clinicians won't adopt" | "The last EMR rollout failed" | Change-management plan + scribe demo |
| "Legal / regulatory" | "I don't have air cover" | MoH submission package + compliance dossier |
| "Just the patient app first" | "I want to defer the real decision" | Name the real board-level pain |

---

## Appendix B: Do-not-say list

Do not say these in a Middle-East healthcare meeting. Each is a credibility loss.

- *"Trust me."* — Show the artifact.
- *"Our AI is smarter than the doctor."* — Never. It assists; the clinician decides.
- *"We'll figure it out during implementation."* — Have the answer or say you will send it same-day.
- *"Epic is bad."* — Epic is excellent. It is wrong for **this** deployment.
- *"Free trial."* — Paid pilot with success criteria.
- *"Just sign here."* — Always leave with a next meeting, not a signature ask on the first visit.

---

## Appendix C: Escalation ladder

If an objection is above your authority, escalate — do not improvise.

| Objection type | Escalate to |
|---|---|
| Pricing outside published tiers | Regional sales director |
| Data residency / on-prem architecture | Solutions architect |
| Clinical safety, CDS, ambient scribe | Clinical informaticist |
| MoH / regulatory submission | Head of compliance |
| Contract, IP escrow, DPA changes | Legal counsel |
| Executive-level reference call | Cybercom CEO office |

End of playbook. Good hunting.
