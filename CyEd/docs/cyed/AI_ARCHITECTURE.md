# CyED — AI Architecture

How CyED's AI is built today, and how it scales. Everything below is **real code**
in `products/cyed/*` — the AI works deterministically without an LLM and upgrades
to a live model behind the same contracts when `CYED_LLM_ENABLED=1`.

## Principles (enforced in code)
- **Grounded, not free-form** — retrieval over the ACARA registry; agents refuse
  off-curriculum requests.
- **Privacy-first** — PII stripped before any model call (`ai_agents/anonymize.py`);
  `no_train` on every request; AU data residency at deploy.
- **Human-in-the-loop** — teacher generations are `pending_review` artifacts;
  integrity + at-risk + wellbeing flags are advisory, decided by a human.
- **Transparent** — rule-based analytics list their factors; every AI call is logged
  (`AgentInteractionLog`).

## Component map (in-process today → microservices later)

```
                     ┌───────────────────────────────────────────┐
   Next.js web  ───▶ │  Django API (core.urls, DRF)              │
   (proxy)           │  RBAC + consent gate (governance/access)  │
                     └───────────────┬───────────────────────────┘
        ┌───────────────────────────┼─────────────────────────────────┐
        ▼                           ▼                                 ▼
┌───────────────┐        ┌────────────────────┐            ┌────────────────────┐
│ Pedagogy AI   │        │ Predictive         │            │ Grounding & Safety │
│ ai_agents/    │        │ analytics/         │            │ retrieval.py       │
│ • tutor       │        │ • at-risk (svc)    │            │ anonymize.py       │
│ • socratic    │        │ • fee_analytics    │            │ llm.py (Anthropic  │
│ • teacher_tools│       │ substitution/      │            │  seam, env-gated)  │
│ • integrity   │        │ • build_plan       │            │ curriculum (ACARA) │
└───────┬───────┘        └─────────┬──────────┘            └─────────┬──────────┘
        │  HITL (GeneratedArtifact) │ advisory bands                 │ ACARA index
        ▼                           ▼                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PostgreSQL (tenant-scoped)   +   Notifications (in-app now; SMS/WhatsApp seam) │
└──────────────────────────────────────────────────────────────────────────────┘
```

## The LLM seam (`ai_agents/llm.py`)
Single choke point for all model calls: `generate(question, context, model_name, system)`.
- Off by default → deterministic grounded fallback (the product always works).
- On → Anthropic Messages API (`claude-sonnet-5` default), grounding-enforced system
  prompt, fail-safe on error. Swap providers here without touching agents.

## Retrieval (`ai_agents/retrieval.py` + `curriculum/`)
Term-overlap ranker over `CurriculumOutcome` (tenant-scoped, code short-circuit).
Portable to Postgres full-text / pgvector for scale without changing callers.
The full ACARA v9 dataset loads via `manage.py import_curriculum`.

## Feature → module index
| AI feature | Where | Status |
|---|---|---|
| Teacher lesson/rubric/differentiator | `ai_agents/teacher_tools.py` + HITL | ✅ |
| Student Socratic tutor | `ai_agents/socratic.py` (`/ai/tutor/socratic/`) | ✅ |
| At-risk early warning | `analytics/services.py` | ✅ |
| Predictive fee / cash-flow | `analytics/fee_analytics.py` (`/analytics/fee-risk/`) | ✅ |
| Teacher substitution | `substitution/services.py` (`/substitution/plans/generate/`) | ✅ |
| Wellbeing sentiment | `wellbeing/sentiment.py` (`/wellbeing/checkins/`) | ✅ |
| Fee reminders / installments | `billing/services.py` | ✅ |
| Bus safety (RFID → parent) | `transport/signals.py` | ✅ (event flow; live GPS = device seam) |
| Facial attendance · route optimisation · OCR intake · WhatsApp · AI scribe (STT) | — | ⚠️ device/provider/model seams |

## Scaling path (when load requires it)
1. Extract `ai_agents` + `analytics` behind the same DRF contracts into a FastAPI
   service; keep `llm.py`/`retrieval.py` as the shared interface.
2. Move retrieval to pgvector; add a small embedding worker.
3. Push notifications + reminders onto Celery/Redis (already configured, eager in dev).
4. Add provider adapters for SMS/WhatsApp/STT/OCR behind the existing seams.
