# CyMed Demo Laptop Setup

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom devops
**Reader:** Sales Engineer with a new laptop and a plane in 2 hours

---

## Prerequisites

- **Python 3.12** installed and on `PATH` — https://www.python.org/downloads/
- **Git** — https://git-scm.com/downloads
- **VS Code** recommended (not required)
- 3 GB free disk
- Internet during setup (offline after)

Verify:
```bash
python --version    # or: py -3.12 --version
git --version
```

---

## One-command install

### Windows PowerShell

```powershell
git clone https://github.com/cybercom/cymed.git
cd cymed
.\tools\demo\setup-windows.ps1
```

### macOS / Linux

```bash
git clone https://github.com/cybercom/cymed.git
cd cymed
bash tools/demo/setup-unix.sh
```

**What the script does (idempotent):**
1. Creates `.venv/` virtualenv
2. `pip install -r requirements.txt`
3. Runs Django migrations against SQLite dev DB (`dev_smoke.db`)
4. Seeds Specialized Hospital Amman tenant (200 patients · 300 encounters · 8 facilities · 60 practitioners · ~41 K JOD in bills)
5. Prints boot instructions

Running twice: safe. Detects existing venv, skips re-install. Reseed wipes tenant first (via `--wipe`).

---

## Two-command boot (for every demo)

Terminal 1 — Django API on `http://127.0.0.1:8000`:
```bash
# macOS / Linux
source .venv/bin/activate && python tools/demo/run_local_demo.py

# Windows
.\.venv\Scripts\Activate.ps1 ; python tools\demo\run_local_demo.py
```

Terminal 2 — static demo shell on `http://127.0.0.1:8090`:
```bash
python -m http.server 8090 -d tools/demo
```

Open in browser: **http://127.0.0.1:8090/demo_portal.html**

Kill both with `Ctrl-C` when the meeting ends.

---

## Reset the demo between meetings (one command)

```bash
python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='core.settings'
os.environ['DJANGO_DEBUG']='True'
os.environ['DJANGO_SECRET_KEY']='dev-unsafe'
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':'dev_smoke.db'}}
django.setup()
from django.core.management import call_command
call_command('seed_specialized_hospital', '--wipe', '--patient-count=200', '--encounter-count=300')
"
```

Wipes any stray data from the last demo (bills touched by scenarios, ad-hoc rows).

---

## Offline mode (no Wi-Fi at the client site)

The demo works fully offline as long as:
- Local Django was started BEFORE Wi-Fi dropped (Google Fonts CDN in `demo_portal.html` will silently fail to load — replace with system font stack for full offline)
- No calls to real vendor sandboxes (they'd need internet)

Cloud demo (artifact URL) requires internet — hand out laptop-hosted version instead.

If the client site's Wi-Fi is captive-portal or blocks Google Fonts: switch to `--offline` mode by editing `tools/demo/demo_portal.html` and stripping the fonts.googleapis.com line at the top.

---

## When to open the artifact URL vs the local server

| Situation | Use |
|---|---|
| First cold outreach, sending link in email | **Artifact URL** — https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656 |
| Zoom / Teams call, screen-sharing | **Artifact URL** — client sees exactly what you see, no local complexity |
| On-site meeting, projector | **Local server** — shows real API calls in DevTools if IT asks |
| Technical deep-dive with hospital IT | **Local server + Swagger UI** at http://127.0.0.1:8000/api/docs/ |
| Post-meeting UAT handoff | **Artifact URL + UAT checklist artifact** — https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69 |

---

## Troubleshooting — top 8 issues

| # | Symptom | Fix |
|---|---|---|
| 1 | `python: command not found` | Install Python 3.12; on Windows use `py -3.12` instead of `python` |
| 2 | `pip install` hangs | Behind proxy; run `pip config set global.proxy http://your-proxy` |
| 3 | `django.core.exceptions.ImproperlyConfigured: multiple filesystem locations for platform` | You cloned a stale branch; run `git pull origin main` and rerun setup |
| 4 | Port 8000 already in use | Someone else's Django. `lsof -i :8000` (mac) / `netstat -ano | findstr :8000` (Windows) → kill PID |
| 5 | Port 8090 gives WinError 10013 | Windows reserves 8080/8090 sometimes. Try 8091: `python -m http.server 8091 -d tools/demo` |
| 6 | Demo shell shows "offline" chip in header | Django is not up on 8000, or blocked by firewall. Restart terminal 1 |
| 7 | Fonts look wrong / fallback showing | Google Fonts blocked at client site. Doesn't affect functionality, but flag it |
| 8 | `python manage.py check` shows model errors after `git pull` | Old migrations conflict; delete `dev_smoke.db` and rerun setup |

---

## Content to have open BEFORE the meeting

Browser tabs (in this order — left to right):
1. Cloud artifact demo — https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656
2. UAT checklist artifact — https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69
3. Local demo shell — http://127.0.0.1:8090/demo_portal.html
4. Swagger UI — http://127.0.0.1:8000/api/docs/
5. Pricing PDF — `docs/commercial/PRICING.md` (open in Markdown viewer or export to PDF)
6. Pilot agreement — `docs/commercial/PILOT_AGREEMENT.md`

Terminal windows (Ctrl+B to split):
- One with the reseed one-liner ready to paste (for a mid-demo reset)
- One running the scenarios script if the client wants to see 10 patient journeys end-to-end

---

## Post-meeting handoff to CRM

Within 24h of the meeting (see `docs/sales/QUALIFICATION_SCRIPT.md` for the data-capture checklist):
1. Log meeting notes in CRM
2. Attach any signed / marked-up UAT checklist
3. Log tier (A / B / C / D per rubric)
4. Set the next-step task with owner and due date
5. Send the follow-up email (template 4 in `docs/sales/EMAIL_TEMPLATES.md`)
6. If A-tier: draft pilot proposal within 48h using `docs/commercial/PILOT_AGREEMENT.md`
7. If B-tier: schedule the 30-day nurture touchpoint (template 5)

---

## Rotation SLA

The demo laptop image should be refreshed every 2 weeks:
- `git pull origin main`
- Rerun `setup-unix.sh` / `setup-windows.ps1`
- Verify all 5 tabs of the demo portal load
- Run 3 scenarios to smoke-test

Owner: whichever SE is on rotation. Log in `docs/hardening/PILOT_READINESS_CHECKLIST.md`.
