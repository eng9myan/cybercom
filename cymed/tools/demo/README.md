# CyMed Demo Portal — Specialized Hospital Amman

A single-file HTML demo shell for showcasing CyMed at Specialized Hospital
(Amman). Renders 5 tabs (Reception, Clinician Workstation, Patient Portal,
Command Center, Payment & Insurance) with live-fetch to the CyMed backend
and a graceful fallback to bundled sample data when offline.

## Files

- `demo_portal.html` — the demo. Single self-contained HTML file, no build
  step. Uses Tailwind via CDN and vanilla JS + `fetch`.
- `README.md` — this file.

## Open

Just double-click `demo_portal.html`, or:

```bash
# Windows
start D:\cybercom\cymed\tools\demo\demo_portal.html

# Or serve for a cleaner origin (any static server works)
python -m http.server 8080 --directory D:\cybercom\cymed\tools\demo
# then open http://localhost:8080/demo_portal.html
```

## Live API pointer

By default the demo fetches from `http://localhost:8000`. To point it at
another CyMed instance, set `window.CYMED_API_BASE` **before** the app
boots — either inject a `<script>window.CYMED_API_BASE="..."</script>`
above the closing `</head>`, or wrap the file in an iframe from a page
that defines the constant.

Endpoints the demo will try (all optional — sample data is used on
failure):

| Endpoint                                | Tab              |
| --------------------------------------- | ---------------- |
| `GET  /api/demo/reception/`             | Reception        |
| `GET  /api/demo/clinician/active-patient/` | Clinician     |
| `GET  /api/demo/patient/me/`            | Patient Portal   |
| `GET  /api/demo/command-center/`        | Command Center   |
| `GET  /api/demo/payments/`              | Payment & Ins.   |
| `POST /api/demo/adjudicate/`            | Payment (button) |

The header shows a small `live` / `offline` chip so the operator always
knows which mode is in effect.

## Seed first

The demo expects the CyMed seed script to have run against the target
tenant before it will show anything meaningful from the live API. Run
your usual seed step first (e.g. the tenant provisioning + demo-data
scripts in `tools/`), then start the backend and reload the page.

Until then — or when demoing on a plane — the built-in sample dataset
covers all five tabs with realistic Specialized-Hospital-Amman content:
JCI CCPC cardiac case, JOD amounts, the 11 Jordanian insurers, 21 ORs,
28 NICU incubators, and 265-bed occupancy figures.

## Language

Toggle EN / AR from the top-right, or press `L`. The whole document
flips to RTL (`<html dir="rtl">`) and every labelled string re-renders
from the bundled i18n dictionary.

## Tab shortcuts

Keys `1`–`5` jump between tabs. `L` toggles language.

## Brand

Gradient header `#0062CC → #00D4AA`, glassmorphism cards with
`backdrop-filter: blur`. All colors and radii live in the `<style>`
block at the top of the HTML file — easy to rebrand for a partner
demo.

## Disclaimer

All patient names, MRNs, claim numbers, and amounts in the bundled
sample data are simulated for demonstration only.
