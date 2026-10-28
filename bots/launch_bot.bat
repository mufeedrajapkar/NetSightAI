@echo off
setlocal enabledelayedexpansion
title NetSight AI - Distributed Bot Traffic Generator

echo ================================================================
echo           NETSIGHT AI - MULTI-NODE BOT GENERATOR
echo ================================================================
echo.

REM 1. Ask for Target Server IP / URL
set "DEFAULT_SERVER=http://127.0.0.1:5001"
set /p "SERVER_INPUT=Enter Server IP or URL (Press Enter for %DEFAULT_SERVER%): "
if "%SERVER_INPUT%"=="" set "SERVER_INPUT=%DEFAULT_SERVER%"

REM Add http prefix if only IP:Port was typed
echo %SERVER_INPUT% | findstr /i "http://" >nul || echo %SERVER_INPUT% | findstr /i "https://" >nul
if errorlevel 1 (
    set "SERVER_URL=http://%SERVER_INPUT%:5001"
) else (
    set "SERVER_URL=%SERVER_INPUT%"
)

REM 2. Ask for Node Device ID
echo.
set "DEFAULT_DEVICE=PC01"
set /p "DEVICE_ID=Enter Device ID for Dashboard [PC01, PC02, PC03, PC04] (default: %DEFAULT_DEVICE%): "
if "%DEVICE_ID%"=="" set "DEVICE_ID=%DEFAULT_DEVICE%"

REM 3. Select Bot Tier
echo.
echo Select Bot Tier to execute:
echo   [1] Tier 1: Naive Bot (Fixed delay, single hardcoded UA)
echo   [2] Tier 2: Jittered Bot (Uniform random delay, rotating UA)
echo   [3] Tier 3: Human-Mimicking Bot (Empirical timing + thinking pauses)
echo   [4] Tier 4: Adversarial Bot (Feature-space shaping, lognormal delays)
echo   [5] Human Recorder (Record real manual human traffic)
echo.
set /p "TIER_CHOICE=Choose an option (1-5): "

echo.
echo [*] Target Server : %SERVER_URL%
echo [*] Device ID     : %DEVICE_ID%
echo ================================================================
echo.

if "%TIER_CHOICE%"=="1" (
    echo [*] Launching Tier 1 Naive Bot...
    python "%~dp0tier1_naive.py" --target-url "%SERVER_URL%" --device-id "%DEVICE_ID%" --duration 60 --interval 0.2
) else if "%TIER_CHOICE%"=="2" (
    echo [*] Launching Tier 2 Jittered Bot...
    python "%~dp0tier2_jittered.py" --target-url "%SERVER_URL%" --device-id "%DEVICE_ID%" --duration 60 --min-interval 0.15 --max-interval 0.45
) else if "%TIER_CHOICE%"=="3" (
    echo [*] Launching Tier 3 Human-Mimicking Bot...
    python "%~dp0tier3_mimicking.py" --target-url "%SERVER_URL%" --device-id "%DEVICE_ID%" --duration 60
) else if "%TIER_CHOICE%"=="4" (
    echo [*] Launching Tier 4 Adversarial Bot...
    python "%~dp0tier4_adversarial.py" --target "%SERVER_URL%" --device-id "%DEVICE_ID%" --requests 30
) else if "%TIER_CHOICE%"=="5" (
    echo [*] Launching Human Traffic Recorder...
    python "%~dp0human_recorder.py" --target-url "%SERVER_URL%"
) else (
    echo [!] Invalid selection. Defaulting to Tier 1...
    python "%~dp0tier1_naive.py" --target-url "%SERVER_URL%" --device-id "%DEVICE_ID%" --duration 60 --interval 0.2
)

echo.
echo ================================================================
echo [*] Bot session finished. Press any key to exit.
echo ================================================================
pause >nul
