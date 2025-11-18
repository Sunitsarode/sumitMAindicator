@echo off
echo ========================================
echo Starting Live Analyser
echo ========================================
echo.

:: --- Activate Python Environment ---
echo Activating Python Virtual Environment...
call D:\freq\trade\kotak\pyreact\indicenv\Scripts\activate
if %errorlevel% neq 0 (
    echo ❌ Failed to activate Python environment.
    pause
    exit /b
)

:: --- Start Backend ---
echo [1/2] Starting Backend Server...
start "Backend Server" cmd /k "cd backend && call D:\freq\trade\kotak\pyreact\indicenv\Scripts\activate && python app.py"
timeout /t 3 >nul

:: --- Start Frontend ---
echo [2/2] Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

:: --- Info ---
echo.
echo ========================================
echo ✅ Both servers are starting...
echo Backend:  http://localhost:5001
echo Frontend: http://localhost:3000
echo ========================================
echo.
pause

:: --- Stop Servers on key press ---
echo Stopping servers...
taskkill /FI "WINDOWTITLE eq Backend Server*" /F >nul
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F >nul
echo All servers stopped.

