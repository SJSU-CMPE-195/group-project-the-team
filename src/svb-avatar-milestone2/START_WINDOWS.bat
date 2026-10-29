@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (
  echo Node.js not found. Install Node.js 22.12 or newer from https://nodejs.org/
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo npm not found. Reinstall Node.js with npm.
  pause
  exit /b 1
)
if not exist "node_modules\three" (
  echo Installing dependencies on first run. Internet access is required for npm install.
  call npm install
  if errorlevel 1 (
    echo npm install failed. Check internet connection and retry.
    pause
    exit /b 1
  )
)
echo Starting Three.js avatar at http://127.0.0.1:5173/
call npm run dev
if errorlevel 1 pause
