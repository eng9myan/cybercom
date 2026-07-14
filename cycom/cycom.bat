@echo off
rem Copyright (c) CyberCom. All rights reserved.
rem Cycom ERP Command Line Utility wrapper.

if "%1"=="compliance" (
    if "%2"=="scan-branding" (
        python "%~dp0compliance_scanner.py" compliance scan-branding
        exit /b %errorlevel%
    )
)

echo Usage: cycom compliance scan-branding
exit /b 1
