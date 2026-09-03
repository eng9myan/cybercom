# CyMed × Specialized Hospital Amman — Client Access

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom demo lead

---

## Three access paths — pick per audit rigour

### 1. Cloud-hosted (fastest, no infra)

- **Demo UI:** https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656
- **UAT checklist:** https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69
- **Share** — open each URL in Claude, top-right **Share** → **Anyone with the link** OR invite client emails specifically. Artifacts are private until you share.
- **Client capability:** view + navigate + interact + leave inline comments per element
- **What is stubbed:** every API is bundled JSON — nothing hits a live server
- **Best for:** initial visual walk-through, first-impression audit, on-the-go review

### 2. Live local backend — ngrok tunnel

Client hits YOUR laptop from their office through a public HTTPS tunnel. All real API calls, real seeded database, real bills materialising.

Prerequisites:
- Django dev server up on `127.0.0.1:8000` (already running — task `bng66jzpy`)
- Static demo shell up on `127.0.0.1:8090` (already running — task `bj5hvyzod`)
- ngrok account (free tier works — https://ngrok.com/download)

Install ngrok:
```bash
# Windows
winget install ngrok
# or download from https://ngrok.com/download and unzip to PATH

# authenticate one-time (from ngrok dashboard)
ngrok config add-authtoken YOUR_TOKEN_HERE
```

Expose both servers (two terminals, or `--config` file):

```bash
# terminal 1 — API backend
ngrok http 8000 --domain=cymed-api-demo.ngrok.dev
```

```bash
# terminal 2 — demo shell
ngrok http 8090 --domain=cymed-shell-demo.ngrok.dev
```

Free tier gives you random subdomains like `https://ab12cd.ngrok.dev`. Paid tier lets you reserve stable names.

Send client:
```
Demo shell:  https://<your-ngrok-shell>.ngrok.dev/demo_portal.html
API docs:    https://<your-ngrok-api>.ngrok.dev/api/docs/
Tenant UUID: 4403df62-d91e-4f7a-8b26-a46118154bf4
Sample curl:
  curl -H "X-Tenant-ID: 4403df62-d91e-4f7a-8b26-a46118154bf4" \
       https://<your-ngrok-api>.ngrok.dev/api/v1/rcm/claims/
```

Kill tunnel: **Ctrl-C** in each ngrok terminal. Your laptop then disappears from the internet.

**Security:**
- Only expose while client is testing. Kill tunnel immediately after.
- Do not use with real patient data. Demo tenant only.
- Add basic auth to ngrok if you want a second lock:
  ```bash
  ngrok http 8000 --basic-auth "client:strong-password-here"
  ```

### 3. Live in-person / Zoom walkthrough

Cybercom engineer runs the seed + scenarios script while sharing screen. Client watches actual DB writes.

```bash
cd D:/cybercom/cymed
# reseed with production-scale numbers
python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='core.settings'
os.environ['DJANGO_DEBUG']='True'; os.environ['DJANGO_SECRET_KEY']='dev-unsafe'
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':'dev_smoke.db'}}
django.setup()
from django.core.management import call_command
call_command('seed_specialized_hospital', '--wipe', '--patient-count=200', '--encounter-count=300')
"

# run 10 end-to-end scenarios in real time
USE_SQLITE=1 python tools/demo/scenarios_specialized_hospital.py
```

Talk-track: `docs/demo/DEMO_RUNBOOK.md` (30-min minute-by-minute).

---

## Sharing checklist

- [ ] Artifact URLs shared with correct visibility (link-only vs email-invite)
- [ ] `UAT_TEST_PLAN.md` PDF exported + sent
- [ ] `DEMO_STATUS.md` sent (client knows what's stubbed)
- [ ] Zoom / Teams scheduled if live audit chosen
- [ ] ngrok tunnel launched only if remote real-API access requested
- [ ] Sign-off block returned + saved to `docs/demo/signoffs/`

---

## Client contact template

**Subject:** CyMed × Specialized Hospital — demo walkthrough + UAT

Attached: 150-point UAT test plan.

Two URLs (click, no login required):
1. Demo UI — https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656
2. UAT checklist — https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69

Header controls: **EN ↔ AR** (Arabic + RTL) · **☀ light / ☾ dark / ⌂ system** · **A- / A / A+** font size.

Sidebar: 10 collapsible groups, 39 modules covering every hospital function — reception, ED, ICU, OR, NICU, wards, pharmacy, lab, imaging, blood bank, RCM, finance, HR, CSSD, biomed, quality, patient app, executive dashboards, regulatory alignment.

Every screen grounded in your real world: 265 beds, 21 ORs, 28 NICU incubators, Cardiac CoE, JCI × 6, 11 accepted insurers including RMS, JOD/JoFotara e-invoicing.

Walk the 39 modules, tick the checklist, sign the last page.

For live-system audit (real database writes, real API calls, real bills materialising): schedule a 60-minute Zoom — we'll run 10 patient journeys end-to-end and expose the API through Swagger UI.

Findings channel: reply to this email, OR leave inline comments on any element in the demo (right-click / three-dot menu → Comment).

---

## Emergency stop

Client sees something they should not, or the demo goes weird:

- **Kill ngrok tunnels** — Ctrl-C each terminal
- **Rotate artifact URLs** — republish with new file paths (breaks the old URLs)
- **Kill Django + static servers** — kill background tasks `bng66jzpy` and `bj5hvyzod`
- **Wipe demo DB** — `rm D:/cybercom/cymed/dev_smoke.db`
