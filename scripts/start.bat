@echo off
setlocal

echo 🌆 Starting City Operations Center...

if "%OPENAI_API_KEY%"=="" (
    echo ⚠️  Warning: OPENAI_API_KEY not set!
    echo    Set it with: set OPENAI_API_KEY=sk-your-key-here
    exit /b 1
)

set MODE=%1
if "%MODE%"=="" set MODE=unified

set PORT=%2
if "%PORT%"=="" set PORT=8080

set FRONTEND_PORT=%3
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=3000

echo Mode: %MODE%
echo API Port: %PORT%
echo Frontend Port: %FRONTEND_PORT%

start "Frontend" python -m http.server %FRONTEND_PORT% --directory frontend
start "Backend" python src/main.py --mode %MODE%

echo.
echo ✅ City Operations Center is running!
echo    Dashboard: http://localhost:%FRONTEND_PORT%/dashboard.html
echo    API:       http://localhost:%PORT%
echo    Docs:      http://localhost:%PORT%/_schema
echo.
pause
