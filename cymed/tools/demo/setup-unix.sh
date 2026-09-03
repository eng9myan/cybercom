#!/usr/bin/env bash
# CyMed demo laptop bring-up — macOS / Linux.
# Idempotent: safe to run twice.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/../.." && pwd)"   # repo root (D:/cybercom/cymed equivalent)
cd "$HERE"

PY="${PYTHON:-python3.12}"
command -v "$PY" >/dev/null 2>&1 || { echo "ERROR: python3.12 not found. Install from python.org."; exit 1; }

echo "[1/5] Creating virtualenv…"
[ -d .venv ] || "$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/5] Installing requirements…"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt || pip install --quiet Django djangorestframework django-cors-headers drf-spectacular django-filters httpx celery redis

echo "[3/5] Applying migrations to SQLite dev DB…"
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY=dev-unsafe
"$PY" -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='core.settings'
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':'dev_smoke.db'}}
django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
"

echo "[4/5] Seeding Specialized Hospital Amman demo tenant…"
"$PY" -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='core.settings'
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':'dev_smoke.db'}}
django.setup()
from django.core.management import call_command
call_command('seed_specialized_hospital', '--wipe', '--patient-count=200', '--encounter-count=300')
"

echo "[5/5] Done."
cat <<EOF

CyMed demo ready.

Start Django on :8000 (background, kill with Ctrl-C):
  source .venv/bin/activate && python tools/demo/run_local_demo.py

Static demo shell on :8090 (second terminal):
  python -m http.server 8090 -d tools/demo

Open http://127.0.0.1:8090/demo_portal.html in your browser.
Cloud demo (no local needed): https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656

EOF
