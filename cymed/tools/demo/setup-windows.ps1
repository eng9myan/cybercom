# CyMed demo laptop bring-up — Windows PowerShell.
# Idempotent: safe to run twice.
$ErrorActionPreference = "Stop"

$here = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $here

$py = if ($env:PYTHON) { $env:PYTHON } else { "py -3.12" }
try { & $py.Split(" ")[0] $py.Split(" ")[1] -V | Out-Null } catch {
    Write-Host "ERROR: Python 3.12 not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

Write-Host "[1/5] Creating virtualenv…"
if (-not (Test-Path ".venv")) { & $py.Split(" ") -m venv .venv }
. .\.venv\Scripts\Activate.ps1

Write-Host "[2/5] Installing requirements…"
python -m pip install --quiet --upgrade pip
try { python -m pip install --quiet -r requirements.txt }
catch { python -m pip install --quiet Django djangorestframework django-cors-headers drf-spectacular django-filters httpx celery redis }

Write-Host "[3/5] Applying migrations to SQLite dev DB…"
$env:DJANGO_DEBUG = "True"
$env:DJANGO_SECRET_KEY = "dev-unsafe"
python -c @'
import os, django
os.environ["DJANGO_SETTINGS_MODULE"]="core.settings"
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {"default": {"ENGINE":"django.db.backends.sqlite3","NAME":"dev_smoke.db"}}
django.setup()
from django.core.management import call_command
call_command("migrate", verbosity=0)
'@

Write-Host "[4/5] Seeding Specialized Hospital Amman demo tenant…"
python -c @'
import os, django
os.environ["DJANGO_SETTINGS_MODULE"]="core.settings"
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {"default": {"ENGINE":"django.db.backends.sqlite3","NAME":"dev_smoke.db"}}
django.setup()
from django.core.management import call_command
call_command("seed_specialized_hospital", "--wipe", "--patient-count=200", "--encounter-count=300")
'@

Write-Host "[5/5] Done." -ForegroundColor Green
Write-Host ""
Write-Host "CyMed demo ready."
Write-Host ""
Write-Host "Start Django on :8000 (terminal 1):"
Write-Host "  .\.venv\Scripts\Activate.ps1 ; python tools\demo\run_local_demo.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Static demo shell on :8090 (terminal 2):"
Write-Host "  python -m http.server 8090 -d tools\demo" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open http://127.0.0.1:8090/demo_portal.html"
Write-Host "Cloud demo: https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656" -ForegroundColor Cyan
