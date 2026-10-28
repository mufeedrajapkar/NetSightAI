@echo off
setlocal enabledelayedexpansion

title NetSight AI - Launch Controller

echo ====================================================
echo             NETSIGHT AI - LAUNCH CONTROLLER
echo ====================================================
echo.

REM 1. Locate project root directory
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

if exist "%ROOT_DIR%\CN\web\backend_server.py" goto dir_found
if exist "%ROOT_DIR%\sentinelnet\CN\web\backend_server.py" set "ROOT_DIR=%ROOT_DIR%\sentinelnet"
if exist "%ROOT_DIR%\CN\web\backend_server.py" goto dir_found

echo [!] Error: Could not locate backend_server.py in current directory or sentinelnet subfolder.
pause
exit /b 1

:dir_found
cd /d "%ROOT_DIR%"

REM 2. Set default environment variables if not set
if not defined SENTINELNET_API_KEY set "SENTINELNET_API_KEY=sentinelnet_secure_secret_key_2026"
if not defined SENTINELNET_SERVER_URL set "SENTINELNET_SERVER_URL=http://127.0.0.1:5001"

REM 3. Determine Python executable
set "PYTHON_CMD="
if exist "%ROOT_DIR%\venv\Scripts\python.exe" (
    set "PYTHON_CMD=%ROOT_DIR%\venv\Scripts\python.exe"
    echo [*] Using virtualenv Python: venv\Scripts\python.exe
) else if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%ROOT_DIR%\.venv\Scripts\python.exe"
    echo [*] Using virtualenv Python: .venv\Scripts\python.exe
) else (
    set "PYTHON_CMD=python"
    echo [*] Using system Python
)

"%PYTHON_CMD%" --version >nul 2>nul
if errorlevel 1 (
    echo [!] Error: Python was not found in PATH or virtualenv.
    echo [!] Please install Python 3.10 or newer and add it to PATH.
    pause
    exit /b 1
)

REM 4. Verify Node.js / npm
where npm >nul 2>nul
if errorlevel 1 (
    echo [!] Error: npm was not found in PATH.
    echo [!] Please install Node.js from https://nodejs.org to run the frontend.
    pause
    exit /b 1
)

REM 5. Check if frontend dependencies are installed
if not exist "%ROOT_DIR%\frontend\node_modules" (
    echo [*] Installing frontend npm dependencies...
    cd /d "%ROOT_DIR%\frontend"
    call npm install
    cd /d "%ROOT_DIR%"
)

REM 6. Launch Backend Server in a new window
echo [*] Starting NetSight AI Backend API server on port 5001...
start "NetSight AI - Backend Server" cmd /k "title NetSight AI - Backend Server [Port 5001] && cd /d "%ROOT_DIR%" && set SENTINELNET_API_KEY=%SENTINELNET_API_KEY% && "%PYTHON_CMD%" CN\web\backend_server.py"

REM 7. Launch Frontend Dev Server in a new window
echo [*] Starting NetSight AI Frontend Vite server on port 5173...
start "NetSight AI - Frontend Dashboard" cmd /k "title NetSight AI - Frontend Dashboard [Port 5173] && cd /d "%ROOT_DIR%\frontend" && npm run dev"

REM 8. Wait for servers to initialize and open the browser
echo [*] Waiting for services to initialize...
ping -n 4 127.0.0.1 >nul

echo [*] Opening browser at http://localhost:5173 ...
start http://localhost:5173

echo.
echo ====================================================
echo             NETSIGHT AI IS RUNNING!
echo ====================================================
echo   Backend Server  : http://127.0.0.1:5001
echo   Frontend App    : http://127.0.0.1:5173
echo.
echo   Both services are running in their own windows.
echo   To stop a service, simply close its terminal window
echo   or press Ctrl+C inside it.
echo ====================================================
echo.
echo Press any key to exit this launcher window...
pause >nul
exit /b 0
