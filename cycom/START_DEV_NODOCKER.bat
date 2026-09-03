@echo off
REM ============================================================
REM  Cycom ERP — NO-DOCKER local dev launcher
REM  Backend on SQLite + dev-auth (no Postgres/Redis/Keycloak).
REM  Frontend runs separately: npm --prefix cycom-erp run dev -- --port 7000
REM ============================================================
setlocal
set DJANGO_SETTINGS_MODULE=core.settings_dev
set DJANGO_DEBUG=True
set CYCOM_DEV_AUTH=1

echo [1/4] Migrating SQLite dev database...
python manage.py migrate --noinput || goto :err

echo [2/4] Seeding dev tenant...
python manage.py seed_dev_tenant || goto :err

echo [3/4] Seeding Ready-ERP packs...
python manage.py seed_packs || goto :err

echo [4/4] Starting Django dev server on http://localhost:8090 ...
echo   Then open http://localhost:7000/api/cycom/dev-login to log in.
python manage.py runserver 8090
goto :eof

:err
echo.
echo  Launch failed. See error above.
exit /b 1
