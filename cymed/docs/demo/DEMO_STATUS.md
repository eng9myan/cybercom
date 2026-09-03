# CyMed × Specialized Hospital Amman — Demo Status

**Version:** 1.0
**Date:** 2026-08-19

## What runs today

| Component | Status | Notes |
|---|---|---|
| `manage.py seed_specialized_hospital` | **RUNS** | Creates tenant + 8 facilities + 60 practitioners + 200 patients + 300 encounters + ~410K JOD in bills; verified end-to-end on SQLite |
| `tools/demo/scenarios_specialized_hospital.py` | **RUNS** | 10/10 scenarios execute; scenario 1 mints a real UnifiedBill; scenarios 2–10 print scripted flow with realistic JOD amounts, insurer names, JO context |
| `tools/demo/demo_portal.html` | **OPENS OFFLINE** | 5 tabs (Reception, Clinician Workstation, Patient Portal, Command Center, Payment & Insurance), EN/AR toggle, glassmorphism, fetches from `CYMED_API_BASE` with sample-JSON fallback |
| Django `manage.py check` | **CLEAN** | 0 issues |
| SQLite `migrate` | **CLEAN** | 115 migrations apply |

## What is stubbed / scripted (not live)

| Behaviour | Stub reason | Wire when |
|---|---|---|
| Real-time NPHIES / JoFotara adjudication | Sandbox creds required (per-tenant CCHI mTLS cert for NPHIES; JoFotara issuer registration for JO) | Customer signs pilot MSA, opens sandbox accounts |
| HyperPay charge / refund | Sandbox account credentials | Merchant contract + Mada certification for JO |
| WHO ICD-11 search | Real API — free but requires registration | Register at https://icd.who.int/icdapi, set env vars |
| Aidoc / other AI triage adapters | Vendor SDKs behind commercial contracts | Sign AI vendor DPA + endpoint access |
| Hakeem push (HL7 v2.5 / VistaRPC) | Requires MoH sandbox onboarding | Ministry of Health formal partner-registration in JO |
| Ambient scribe transcription | Whisper stub; real STT needs GPU + LLM tenant provisioning | GPU node + summary LLM tenant (CyGPT or Azure OpenAI) |
| Home-delivery courier dispatch (Aramex/SMSA/Mrsool) | Adapter stubs return canned tracking IDs | Courier API creds |
| SMS / WhatsApp send (marketing + notifications) | Provider stubs (Twilio/Unifonic/360dialog placeholder) | Provider account setup |
| e-Rx signature (HL7 FHIR MedicationRequest signed) | Stub without HSM | HSM procurement + ECDSA key material |

## Exact command sequence

```bash
cd D:/cybercom/cymed

# 1. environment
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY=dev-unsafe

# 2. migrate onto SQLite
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

# 3. run 10 scenarios
USE_SQLITE=1 python tools/demo/scenarios_specialized_hospital.py

# 4. open the demo UI
start tools/demo/demo_portal.html    # Windows
# or: open tools/demo/demo_portal.html   # macOS
```

## Talk track pointers

- Full 30-min minute-by-minute script: `docs/demo/DEMO_RUNBOOK.md`
- Hospital research profile + 21 gaps: `docs/demo/SPECIALIZED_HOSPITAL_AMMAN_PROFILE.md`
- Pricing / commercial pack: `docs/commercial/`
- What we can't sell yet: `docs/hardening/HARDENING_REPORT.md`

## Verification snapshot

- `python manage.py check` → 0 issues
- `python manage.py help | grep seed_specialized_hospital` → command listed
- `python tools/demo/scenarios_specialized_hospital.py` → 10/10 scenarios green
- Real UnifiedBill row minted in SQLite from scenario 1 (verified via query after run)
