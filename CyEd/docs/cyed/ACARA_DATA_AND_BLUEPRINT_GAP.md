# CyED — ACARA Data Sources & Blueprint Gap Analysis

> ## ⚠️ SUPERSEDED in part — 2026-08-11
>
> **Part A.5 ("the gap in CyED, quantified") is out of date and must not be
> quoted.** The full MRAC v9 corpus was ingested on 2026-08-10. Counted directly
> against `cyed_dev.sqlite3` on 2026-08-11:
>
> | | This doc claimed (08-09) | Actual (verified 08-11) |
> |---|---|---|
> | Curriculum outcomes | 56 starter set | **19,592** |
> | — content descriptions | — | 2,764 |
> | — elaborations | field empty | 16,828 |
> | General Capabilities | none, no model | **7** (25,013 outcome links) |
> | Cross-Curriculum Priorities | none, no model | **3** (2,615 outcome links) |
> | Achievement standards | field empty | **68** |
> | MRAC import runs | — | 17 (all vocabularies, CC BY attribution stored per row) |
>
> By learning area: Languages 12,245 · HASS 1,729 · Mathematics 1,289 ·
> The Arts 1,061 · Science 1,047 · English 1,029 · Technologies 660 · HPE 532.
>
> **Parts A.1–A.4 (the verified ACARA source URLs, file shapes and CC BY licence
> terms) remain correct and useful** — they are what the ingester was built
> against. Part B's blueprint gap list is partly stale too: assignment
> submission and auto-marked quizzes (B.2 Tier 1 #1) now exist in the
> `assessment` app. Read `STATUS_2026-08-11_CONSOLIDATED.md` for current state.

**Date:** 2026-08-09
**Inputs:** the shared Gemini thread (*AI Projects for Australia* → full school-ERP
blueprint), plus first-hand verification against acara.edu.au and its data hosts.

---

## Part A — ACARA data: what is actually available (verified)

### A.1 The shared thread's URLs are partly wrong — do not use them

I tested every ACARA link suggested in that thread. Findings:

| Suggested in thread | Reality |
|---|---|
| `scootle.edu.au/ec/p/mrac/2024/04/LA/MAT.json` (used in its Python script) | **Does not exist — fabricated.** Real files are on a different host entirely. |
| `rdf.australiancurriculum.edu.au/api/sparql` | **Not reachable** — returns a Cloudflare bot challenge (HTTP 403). Not the real endpoint. |
| `australiancurriculum.edu.au/machine-readable-australian-curriculum` | ✅ Real — but it is only a landing page; it redirects you to Scootle for the files. |
| `scootle.edu.au/ec/p/mrac_details` | ✅ Real — this is the true download index (blocks scripted fetches; open it in a browser). |

**Copy-pasting that thread's ingestion script would have failed on the first request.**

### A.2 The real MRAC v9 endpoints (verified working, HTTP 200)

Files are hosted on **`vocabulary.curriculum.edu.au`** (a PoolParty vocabulary server).
URL pattern per vocabulary `<SET>` (e.g. `LA/MAT`):

```
HTML      https://vocabulary.curriculum.edu.au/MRAC/2024/04/<SET>.html
RDF/XML   https://vocabulary.curriculum.edu.au/MRAC/2024/04/<SET>/export/MRAC/2024/04/<SET>.rdf
JSON-LD   https://vocabulary.curriculum.edu.au/MRAC/2024/04/<SET>/export/MRAC/2024/04/<SET>.jsonld
SPARQL    https://vocabulary.curriculum.edu.au/PoolParty/sparql/MRAC/2024/04/<SET>
```

Note: SPARQL is **per-vocabulary**, not one global endpoint as the thread claimed.

**Complete set of 18 vocabularies (version 2024/04):**

| Group | Codes |
|---|---|
| Learning Areas (8) | `LA/ART`, `LA/ENG`, `LA/HPE`, `LA/HASS`, `LA/LAN`, `LA/MAT`, `LA/SCI`, `LA/TEC` |
| General Capabilities (7) | `GC/CCT`, `GC/DL`, `GC/EU`, `GC/IU`, `GC/L`, `GC/N`, `GC/PSC` |
| Cross-Curriculum Priorities (3) | `CCP/S` (Sustainability) + Aboriginal & Torres Strait Islander Histories and Cultures, Asia and Australia's Engagement with Asia |

### A.3 Verified download + structure

Downloaded `LA/MAT.jsonld` successfully:

- **HTTP 200**, `application/ld+json`, **3,498,203 bytes (3.5 MB)** — Mathematics alone.
- Shape: a **single-element array** wrapping `{"@graph": [...], "@id": ...}` — *not*
  a bare `@graph` object. The thread's parser (`data.get("@graph")`) would crash here.
- **1,949 graph nodes**, of which **1,289 carry an `AC9…` notation**.
- Vocabulary: **ASN** (`purl.org/ASN/schema/core/`) + **SKOS**. Key predicates:
  `asn:statementNotation` (the AC9 code), `dcterms:description`, `asn:educationLevel`,
  plus `dcterms:rights` / `rightsHolder`.
- Codes include **elaborations** via an `_E<n>` suffix (e.g. `AC9M7N06_E1`) alongside
  the base content description (`AC9M7N06`) — these must be distinguished on import.

### A.4 Licence — clear to use

**CC BY 4.0**, commercial use permitted. Attribution is mandatory:

> © Australian Curriculum, Assessment and Reporting Authority (ACARA) 2010 to present…
> licensed under CC BY 4.0.

Excluded from the licence: ACARA logos/trademarks, photographs and videos, and
teacher-implementation support resources (non-commercial only). Products must also
state that **ACARA does not endorse the product**.

### A.5 The gap in CyED, quantified

| | Now | Required |
|---|---|---|
| Curriculum outcomes loaded | **56** (starter set) | **Thousands** — Mathematics alone has 1,289 AC9 statements |
| Learning areas | 8 (token coverage: Languages = 1 outcome) | 8, fully populated |
| General Capabilities | **none** — no model, no data | 7 vocabularies |
| Cross-Curriculum Priorities | **none** — no model, no data | 3 vocabularies |
| Achievement standards | field exists on the model, **empty** | per learning area × year level |
| Elaborations | field exists, **empty** | `_E` suffixed statements |
| State variants (NESA/VCAA) | field exists, **no data** | separate ingestion |

**`CurriculumOutcome` also cannot represent the real data**: General Capabilities and
Cross-Curriculum Priorities are *many-to-many* against content descriptions, but the
model has no relation for them. Schema work is required before ingestion — this is
not a "just load the file" task.

### A.6 Other ACARA datasets (not yet touched)

From the ACARA Data Access Program — needed for My School / ICSEA-style reporting:
- **All Australian Schools Profile** (ACARA School ID, ICSEA, enrolments, lat/long)
- **School Locations** dataset
- **National Report on Schooling** data portal

CyED's `compliance` app emits NCCD/NAPLAN/census/attendance exports but has **no
ICSEA or ACARA School ID fields**, so its output cannot yet be matched to My School.

---

## Part B — Blueprint gap analysis

The thread describes a best-in-class SMS. Measured against CyED as it stands today.

### B.1 Already built (verified in this codebase)

SIS + admissions · timetable with conflict detection · attendance + guardian
notification · exams/grading · tamper-evident report-card PDFs with per-school
branding · fees + installment billing · **HR, payroll, staff attendance,
accounting, procurement, inventory, assets, document signing** (Phase 0, this week)
· transport + live GPS · library · health · events · visitors · LMS course
structure · **dual AI** (teacher tools + Socratic student tutor, both
curriculum-grounded with HITL review) · at-risk predictive analytics · fee/cash-flow
prediction · substitution engine · RBAC + immutable audit + consent · multi-campus
group layer · field encryption + Postgres RLS · PWA + WCAG basics.

### B.2 Missing — ranked by how much they block a real deployment

**Tier 1 — blocks core daily use**
1. **Assignment submission + online quizzes with auto-grading.** The LMS has
   courses/modules/lessons but **no student submission or assessment engine**. This
   is the single biggest hole for remote/home learning.
2. **Full ACARA load + GC/CCP schema** (Part A) — compliance is unproven without it.
3. **UI for the eight ERP modules built this week** — all API-only today.
4. **Payment gateway** — fees/billing compute correctly but **cannot take money**.
   Currently a seam only.

**Tier 2 — expected by buyers, absent**
5. **Virtual classroom** — no Zoom/Teams/Meet integration, no recordings.
6. **Parent co-educator suite** — no mastery heatmaps, no daily work verification.
7. **Exam operations** — no hall tickets, no seat allocation.
8. **Student lifecycle tail** — no alumni archiving, no Transfer Certificates.
9. **Merit/demerit points** — `BehaviourIncident` exists but has no points system.
10. **SMS / WhatsApp delivery** — env-gated seam, never exercised live.

**Tier 3 — differentiators from the "best-in-class" list**
11. Offline-first sync + low-bandwidth mode (explicitly called out as the key
    COVID lesson) — **not started**.
12. Gamification (badges, streaks); virtual peer hubs / clubs.
13. 24/7 support chatbot for parents.
14. Native iOS/Android apps (PWA only today).
15. Biometric / facial-recognition kiosks (RFID seam exists; vision does not).
16. Hostel / dormitory management — **entire module absent**.
17. Multi-currency.

**Tier 4 — external, cannot be built from code**
IRAP assessment + Essential Eight ML2 (the thread details an AWS mapping), ST4S
certification, penetration test, Entra/Google SSO tenant, app-store presence.

---

## Recommended sequence

1. **Extend the curriculum schema** (GeneralCapability, CrossCurriculumPriority,
   AchievementStandard, elaboration flag, M2M links) — required before any load.
2. **Write a real MRAC ingester** against the verified URLs and the actual
   `[{"@graph": …}]` + ASN/SKOS shape. Include the CC BY attribution string.
3. **Load all 18 vocabularies**, then re-run the ACARA compliance checks.
4. **Build the assignment/quiz engine** — the largest functional hole.
5. **Build UI** for the Phase 0 ERP modules.
6. Then Tier 2.

---

## Verification commands used

```bash
curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}\n" \
  "https://vocabulary.curriculum.edu.au/MRAC/2024/04/LA/MAT/export/MRAC/2024/04/LA/MAT.jsonld"
# 200 application/ld+json 3498203
```
