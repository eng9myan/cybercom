@echo off
REM ---------------------------------------------------------------------------
REM CyEd local development server — no Docker, no Postgres, no Keycloak.
REM
REM Runs the API on :8095, which is the port cyed-web's proxy defaults to, so
REM `npm run dev` in cyed-web talks to it with no further configuration.
REM
REM The two flags below are what core/settings_dev.py requires together before
REM it will accept the fake dev identity. Both are set here and nowhere else:
REM production runs core.settings, which cannot reach the bypass at all.
REM ---------------------------------------------------------------------------
setlocal

cd /d "%~dp0"

set DJANGO_SETTINGS_MODULE=core.settings_dev
set DJANGO_DEBUG=True
set CYED_DEV_AUTH=1

if not exist ".venv\Scripts\python.exe" (
  echo .venv not found. Create it first:
  echo   python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
  exit /b 1
)

REM A second database holding the four-school group demo, so the single-school
REM instance stays untouched:  START_DEV.bat group4
if "%1"=="group4" (
  set CYED_DEV_DB=%~dp0cyed_group4.sqlite3
)

if "%1"=="migrate" (
  .venv\Scripts\python.exe manage.py migrate
  .venv\Scripts\python.exe manage.py seed_cyed_demo
  exit /b %errorlevel%
)

.venv\Scripts\python.exe manage.py runserver 8095 --noreload
