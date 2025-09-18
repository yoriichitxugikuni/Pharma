@echo off
title AI Pharmaceutical Inventory Management System - Auto Startup
color 0A

echo.
echo ============================================================
echo    🚀 AI Pharmaceutical Inventory Management System
echo    Auto Startup Script - Zero Error Setup
echo ============================================================
echo.

echo Starting automatic setup...
echo.

python start_project.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Startup failed. Please check the errors above.
    echo.
    pause
) else (
    echo.
    echo ✅ Project started successfully!
    echo.
)

pause
