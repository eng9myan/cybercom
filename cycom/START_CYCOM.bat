@echo off
title Cycom ERP — All Services Launcher
color 0A

echo.
echo  ================================================
echo   CYCOM ERP — Local Development Environment
echo   CYBERCOM REVOLUTION 2026
echo  ================================================
echo.

REM Kill any processes already on these ports
echo [1/4] Clearing existing processes on ports 4444, 5555, 8888, 8001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":4444 "') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5555 "') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8888 "') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 "') do taskkill /PID %%a /F >nul 2>&1
timeout /t 2 /nobreak >nul

REM Launch Marketing Website on port 4444
echo [2/4] Starting Cycom Marketing Website on http://localhost:4444 ...
start "Cycom Website :4444" cmd /k "cd /d "d:\Cycom ERP\cycom-website" && python -m http.server 4444"

REM Launch FastAPI Micro-Kernel on port 8888
echo [3/4] Starting FastAPI Micro-Kernel on http://127.0.0.1:8888 ...
start "Cycom Micro-Kernel :8888" cmd /k "cd /d "d:\Cycom ERP\core-kernel" && ..\cycom-backend\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8888 --reload"

REM Launch Compliance Gateway on port 8001
echo [4/4] Starting Compliance Gateway on http://127.0.0.1:8001 ...
start "Cycom Compliance Gateway :8001" cmd /k "cd /d "d:\Cycom ERP\compliance-gateway" && ..\cycom-backend\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"

timeout /t 3 /nobreak >nul

REM Open browser tabs
echo.
echo  Opening browser...
start "" "http://localhost:4444"
start "" "http://localhost:5555"
start "" "http://127.0.0.1:8888/docs"

echo.
echo  ================================================
echo   All services launched in separate windows.
echo   Close those windows to stop the services.
echo  ================================================
echo.
pause
