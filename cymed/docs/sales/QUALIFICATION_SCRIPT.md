# CyMed Qualification Script — BANT + MEDDIC

| Field       | Value                              |
|-------------|------------------------------------|
| Version     | 1.0                                |
| Date        | 2026-08-26                         |
| Owner       | Cybercom sales enablement          |
| Audience    | Account Executive (pre-meeting)    |
| Duration    | 45 min discovery call              |
| Product     | CyMed by Cybercom                  |
| Markets     | Jordan (primary), KSA, UAE         |

Related documents: [Elevator pitch](./ELEVATOR_PITCH.md) · [Email templates](./EMAIL_TEMPLATES.md) · [Pricing sheet](./PRICING.md) · [Cloud demo](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656) · [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69)

---

## How to use this script

Read on the way in. Do not read it in the room. Sections 1 (Opening) and 6 (Disqualification) are non-negotiable. Everything else is a prompt bank — pick what the conversation earns.

Target outcomes of the call, in order of priority:
1. Confirm this is an A/B/C tier account (see section 7).
2. Identify the economic buyer and at least one internal champion.
3. Book the next step (technical demo, site visit, or exit).

---

## 1. Opening (30 seconds)

Say verbatim, adapted to the honorific of the person on the line:

> "Doctor [name], thank you for the time. I am [rep] from Cybercom. We build CyMed, a Middle East healthcare platform used by hospitals for clinical, revenue-cycle, and patient-experience workflows on one system. My goal today is not to demo. It is to understand your environment and see whether a 90-day paid pilot would be useful to you. May I ask a few questions before I share anything?"

Wait for the yes. Do not proceed without it.

If they open with a question about price or features, park it:

> "I will answer that in detail, and I have a one-page sheet I will leave with you. Ten minutes of context from you first will make my answer worth your time."

---

## 2. Situation questions (open, ordered)

Ask in this order. Do not skip; do not rearrange. Each answer feeds a BANT or MEDDIC slot later. Take notes verbatim where possible.

### Current environment

1. What HIS or EMR do you run today, and which modules are actually in daily use versus shelfware?
2. Which departments are on the same system, and which run on paper, Excel, or a separate vendor?
3. When was your last major HIS decision, and what drove it?

### Pain and outcomes

4. If we speak again in twelve months and you are happy, what will be measurably better — clinical, financial, or patient-experience?
5. What is the single workflow that costs you the most every week today?
6. Where does revenue leak — denials, undercoding, missed charges, or claim lag?

### Organizational scale

7. How many active providers bill under this facility, and how many beds, ORs, and outpatient rooms are in scope?
8. Is this decision for a single facility, a group, or a network with cross-facility referrals?

### Decision context

9. Who was the last vendor you evaluated and did not choose, and why?
10. How does a decision of this size normally move through your organization — board, medical director, family owners, ministry?
11. What is the fiscal calendar you buy against, and where are we in it?
12. If nothing changes for another year, what is the cost of standing still?

Middle-East-specific probes to weave into 8 through 10:

- "Who is the ultimate signatory — the family board, the CEO, or the medical director?"
- "Does Ministry of Health approval apply for this rollout, or is it internal-only?"
- "Is the facility part of a family holding, a listed group, or a Ministry-linked entity? Governance changes what we prepare."
- "For the KSA scope specifically — is CBAHI accreditation in progress, and does NPHIES onboarding sit with you or with a partner?"

---

## 3. BANT layer

Score each letter Yes / Partial / No / Unknown in your notes. A qualified deal needs Yes or Partial on all four.

### 3.1 Budget

| Question | What you are listening for |
|---|---|
| "Is there a capex or opex line for HIS in this fiscal year?" | Explicit line item, or a shift from capex to opex. |
| "Do you buy healthcare software per-provider, per-bed, or as a capital license?" | Matches our per-active-provider (Clinic/Hospital) and per-room / per-workstation (Lab/Imaging/Pharmacy) model. |
| "For context, our 90-day paid pilot is a fixed fee, and a Standard-tier hospital rollout typically lands in the low-to-mid six figures USD for year one (illustrative — final quote is scoped)." | Their reaction: flinch, nod, or push back. All three are data. |
| "Who signs off spend at that level?" | Feeds Authority. |

Red flag: "We do not have budget but we love it." Downgrade to C and stop investing pre-sales cycles.

### 3.2 Authority

| Question | Purpose |
|---|---|
| "Walk me through who touches this decision — clinical, IT, finance, board." | Map the room. |
| "Who is the ultimate signatory — CEO, CMO, CFO, family board, or Ministry?" | Economic buyer. |
| "Who blocks a decision like this if they say no?" | Anti-champion identification. |
| "May I meet the CIO / CMIO / DHA / MoH liaison in the next call?" | Confirms access. |

### 3.3 Need

| Question | Purpose |
|---|---|
| "Rank in order of urgency: clinical safety, revenue cycle, patient experience, regulatory compliance, or staff retention." | Anchors demo storyline. |
| "What is broken today that a new HIS must fix on day one?" | Non-negotiables. |
| "Are you currently non-compliant on any of: JCI, CBAHI, HCAC, NPHIES, JoFotara, CCHI, or SFDA?" | Compliance wedge. |
| "Do your patients or their families abroad ask to pay bills online today? Can they?" | Sets up patient app and delegated-pay differentiator. |

### 3.4 Timeline

| Question | Purpose |
|---|---|
| "When does the current contract renew, and is there a notice period?" | Real switching window. |
| "If we agreed today, when do you need to go live?" | Realism check. |
| "Is there an event forcing a date — accreditation survey, MoH audit, new facility opening, ownership change?" | Compelling event. |
| "Would a 90-day paid pilot starting in [next quarter] fit your calendar?" | Direct ask. |

---

## 4. MEDDIC layer

Weave into the flow. Do not run as a checklist in the room. Complete all six slots by end of call or in the follow-up.

### M — Metrics

Ask for the number the buyer will present to their own board. Push past qualitative.

- "What is your current denial rate, days in AR, and collection percentage?"
- "Average length of stay, OR utilization, ED door-to-doctor time?"
- "Clinician documentation time per patient — hours per day?"
- "If we could move any one of those by 20 percent (illustrative target), which one would you take?"

Log the metric they name. That is the pilot success criterion.

### E — Economic buyer

- "Who owns the P&L this budget hits?"
- "Has that person personally sponsored an HIS decision before?"
- "What do they care about — margin, growth, accreditation, reputation?"
- Target: a meeting with the EB before the pilot SOW.

### D — Decision criteria

Ask them to list, then rank.

| Common criterion in ME hospitals | Where CyMed wins |
|---|---|
| Arabic RTL and bilingual clinical | Native, not translated |
| NPHIES / JoFotara / CCHI / SFDA readiness | Built in, live integrations |
| Single vendor across clinical, RCM, patient | 39 modules, 10 groups |
| AI documentation and CDS | Ambient scribe is core, not add-on |
| Data residency | JO-regional, on-prem, or cloud |
| Reference sites in region | Flagship: Specialized Hospital Amman |
| Pilot before commit | 90-day paid pilot with success criteria |

If they name a criterion where a competitor wins, mark it and route to solutions engineering — do not fake the answer.

### D — Decision process

- "Walk me through the steps from today to signed contract."
- "Is there a formal RFP? An IT committee? A board meeting cadence?"
- "What has killed a vendor decision here in the past?"
- "Does the family board / owner review, or delegate?"

Draw the process as a numbered list in your CRM. Every step needs an owner and a date.

### I — Identify pain

Convert stated pain into quantified pain.

- "You said denials are a problem. What is the rate this month? What did it cost you last quarter?"
- "You said documentation is heavy. How many clinicians are we talking about, how many hours each, at what fully-loaded cost?"
- "You said patients complain about billing. How many complaints, how many bad reviews, how many switched providers?"

If they cannot quantify, offer to run a joint diagnostic in week one of the pilot.

### C — Champion

A champion has three properties: personal stake, internal credibility, and willingness to sell for you.

Test with:
- "If I sent you a one-page summary tomorrow, would you forward it to [economic buyer] with a note?" (Willingness.)
- "How long have you been at the facility, and has leadership taken your recommendations before?" (Credibility.)
- "What does a successful CyMed rollout do for you personally?" (Stake.)

No champion = no deal. Downgrade to C.

---

## 5. Handling common objections mid-call

| They say | You respond with |
|---|---|
| "We already have [Epic / Cerner / TrakCare]." | "Understood. Most CyMed customers keep a legacy system in one department during pilot. We coexist via HL7 and FHIR. The pilot proves out one workflow — not a rip-and-replace." |
| "We use [InfoMed / DXware / Bayanat]." | "Regional peers we respect. Where CyMed is different: 39 modules on one platform vs 3 to 5 with integration; ambient scribe and AI CDS built in; and cross-facility ecosystem for referrals and payer routing." |
| "Cliniko / Zoho works for us." | "For a small clinic that is a fair choice. If you plan to grow beyond one site, or need NPHIES / JoFotara / accreditation reporting, you will re-platform within 18 months. We would rather you skip that step." |
| "Are you Arabic-first?" | "Yes. RTL is native, not a plugin. Clinical templates, patient communications, and invoices ship in Arabic and English." |
| "What about data residency?" | "Cloud, on-prem, or JO-regional. Your choice per environment. We sign DPA and BAA-equivalent terms." |
| "Show me a reference." | "Specialized Hospital Amman is our Jordan flagship. I can arrange a peer call after the technical demo." |

---

## 6. Disqualification triggers

If any two of these are true, mark the account C tier and set a 6-month reminder. Do not burn pre-sales hours.

| Trigger | Why it matters |
|---|---|
| No budget cycle in next 12 months | Even a perfect fit will not close. |
| A direct competitor signed in the last 90 days | Switching cost inertia too high. |
| CEO / owner leadership transition underway | Decisions freeze. |
| Active M&A or ownership sale | Same. |
| No named clinical or IT sponsor after two calls | No champion. |
| RFP already scored and CyMed is not in the shortlist | We will not win from behind on price alone. |
| Regulatory sanction or accreditation loss pending | Wrong time; revisit post-remediation. |
| Insists on unlimited free pilot | We charge for pilots on principle; success criteria matter. |
| Cannot name a single metric they want to move | Nothing to prove against. |
| Requires custom development we would not resell | Wrong-fit account. |

If exactly one trigger is true, proceed but flag in CRM and align with sales management before the next spend.

---

## 7. Follow-up scoring rubric

Score the account within 24 hours of the call.

| Tier | Criteria | Next step | SLA |
|---|---|---|---|
| A | BANT: 4 Yes. MEDDIC: EB identified, champion confirmed, compelling event named, metric quantified. | Book technical demo + on-site visit. Draft pilot SOW. | 5 business days |
| B | BANT: 3 Yes + 1 Partial. MEDDIC: champion identified, EB known, metric qualitative. | Second discovery with EB present. Send [pricing sheet](./PRICING.md) and one peer reference. | 10 business days |
| C | BANT: 2 or fewer Yes. MEDDIC: no champion, no compelling event, or one disqualification trigger. | Nurture: quarterly touch, newsletter, invite to next Cybercom event. No pre-sales spend. | Quarterly |
| D | Two or more disqualification triggers. | Politely close. Set 6-month revisit. | 6 months |

A-tier deals get a solutions engineer and a solution architect on the next call. B-tier gets an SE only. C and D get the AE only.

---

## 8. Data capture checklist (CRM fields)

Log within 24 hours of the call. Non-negotiable. Fields marked * are required for pipeline stage advance.

### Account

- [ ] * Facility legal name and trade name (EN + AR)
- [ ] * Country and city
- [ ] Facility type: Clinic / Hospital / Lab / Imaging / Pharmacy / Group
- [ ] Ownership: Private / Family / Group / Ministry / Listed
- [ ] Bed count, OR count, outpatient rooms, active providers
- [ ] Current HIS vendor and modules in use
- [ ] Contract renewal date and notice period
- [ ] Accreditation status: JCI / CBAHI / HCAC / other
- [ ] Regulatory scope: NPHIES / JoFotara / Hakeem / CCHI / SFDA / other

### People

- [ ] * Economic buyer: name, title, contact
- [ ] * Champion: name, title, contact, stake
- [ ] Anti-champion: name, title, blocker reason
- [ ] Clinical sponsor: CMO / medical director
- [ ] IT sponsor: CIO / CMIO / IT manager
- [ ] Finance sponsor: CFO / RCM head
- [ ] Signatory: CEO / board / owner / Ministry

### Opportunity

- [ ] * Tier: A / B / C / D
- [ ] * Next step and date
- [ ] Edition scope: Clinic / Hospital / Lab / Imaging / Pharmacy / Ecosystem
- [ ] Deployment: cloud / on-prem / JO-regional
- [ ] Pilot willingness: yes / no / conditional
- [ ] Compelling event and date
- [ ] Named metric and target (the one from MEDDIC-M)
- [ ] Estimated year-1 ACV in USD (mark illustrative until scoped)
- [ ] Competitive set present in the deal
- [ ] Disqualification triggers observed (list)

### Call artifacts

- [ ] Call recording or notes attached
- [ ] Quotes verbatim: their words for pain, their words for success
- [ ] Follow-up email sent (template: see [EMAIL_TEMPLATES.md](./EMAIL_TEMPLATES.md))
- [ ] Cloud demo link sent
- [ ] UAT checklist sent (A-tier only, after technical demo)

---

## 9. Closing the call

Regardless of tier, close the same way. Say verbatim:

> "Thank you. To respect your time — I will send a written summary of what I heard within 24 hours, including the three points you asked me to address. If I got any of it wrong, correct me on email and I will re-send. Our next step is [named next step] on [date]. Is that acceptable?"

Wait for the yes. Then end the call. Do not linger. Do not re-pitch.

---

## Appendix A: Quick-reference card

Print this. Fold it. Keep it in the folio.

| BANT | Ask | Log |
|---|---|---|
| Budget | Line item this FY? | Y / P / N |
| Authority | Ultimate signatory? | Name |
| Need | Top 3 pains, ranked? | Verbatim |
| Timeline | Compelling event? | Date |

| MEDDIC | Ask | Log |
|---|---|---|
| Metrics | Number for the board? | KPI + target |
| Economic buyer | P&L owner? | Name + title |
| Decision criteria | Ranked list? | Top 5 |
| Decision process | Steps to signature? | Numbered |
| Identify pain | Quantified cost? | USD / count |
| Champion | Will they sell for us? | Name + stake |

---

## Appendix B: Competitor cheat sheet

Do not disparage. State facts.

| Competitor | Where they win | Where CyMed wins |
|---|---|---|
| Epic | Global scale, US reference base | ME-native localization, price, deploy time |
| Oracle Health (Cerner) | Large enterprise IT | Single-vendor breadth, patient app, ambient scribe |
| Meditech | Community-hospital fit | Arabic-first, NPHIES / JoFotara built in |
| InterSystems TrakCare | ME footprint, interop | 39 modules on one platform vs core + integrations |
| Allscripts / Altera | Ambulatory strength | Cross-facility ecosystem, medical-tourism module |
| athenahealth | Cloud-native RCM | Full clinical stack, ME regulatory pack |
| InfoMed / DXware (JO) | Local presence, price | Depth of modules, AI CDS, patient experience |
| Bayanat Al-Oula / Alpha (KSA) | KSA installed base | Ambient scribe, cross-provider referrals |
| Medware / Perfect Health | Regional relationships | Modern architecture, cloud and on-prem parity |
| Cliniko / Zoho / DrChrono | Small clinic price point | Any facility beyond a single-provider clinic |

---

## Appendix C: Middle-East governance quick map

Know before you walk in.

| Country | Regulator to name-drop | E-claims / e-invoice | National record |
|---|---|---|---|
| Jordan | HCAC, MoH | JoFotara | Hakeem |
| KSA | CBAHI, SFDA, CCHI | NPHIES | SEHA / national e-health |
| UAE | DHA (Dubai), DoH (Abu Dhabi), MoHAP | Malaffi / Riayati / NABIDH | Same |

Confirm scope on the call. Do not assume a KSA hospital cares about JoFotara or a Jordan clinic cares about NPHIES.

---

End of script.
