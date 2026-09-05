@echo off
REM Naragate quick-start script (Windows)
cd /d "%~dp0"

echo ==============================================
echo   Naragate - quick start
echo ==============================================

REM 1. Docker check
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker is not installed.
  echo Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  echo then open Docker Desktop and re-run this script.
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker is installed but not running.
  echo Open the Docker Desktop app and wait until it shows "Engine running",
  echo then re-run this script.
  pause
  exit /b 1
)

REM 2. Ollama check (optional, only a warning)
where ollama >nul 2>nul
if errorlevel 1 (
  echo [WARN] Ollama not detected.
  echo Naragate needs a local LLM. Install Ollama from https://ollama.com
  echo then pull a model, e.g.:  ollama pull gemma3:12b
) else (
  curl -s -m 3 http://localhost:11434/api/tags >nul 2>nul
  if errorlevel 1 (
    echo [WARN] Ollama is installed but not running.
    echo Start the Ollama app, then pull a model:  ollama pull gemma3:12b
  )
)

REM 3. .env bootstrap
if not exist .env (
  echo Creating .env from .env.example ...
  copy .env.example .env >nul
  echo [WARN] Created .env - you can leave it empty and set keys later in the web UI.
)

REM 4. Start
echo Starting Naragate (first run builds images, this can take a few minutes) ...
docker compose up -d --build
if errorlevel 1 (
  echo [ERROR] docker compose failed. Run:  docker compose logs
  pause
  exit /b 1
)

REM 5. Wait for backend health
set "BACKEND_PORT=%BACKEND_PORT%"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=5678"
echo Waiting for the backend on port %BACKEND_PORT% ...
set "READY=0"
for /L %%i in (1,1,60) do (
  curl -s -m 2 http://localhost:%BACKEND_PORT%/health >nul 2>nul
  if not errorlevel 1 (
    set "READY=1"
    goto :ready
  )
  timeout /t 2 /nobreak >nul
)
:ready
if "%READY%"=="0" (
  echo [ERROR] Backend did not become ready in time.
  echo Run:  docker compose logs backend
  pause
  exit /b 1
)

set "FRONTEND_PORT=%FRONTEND_PORT%"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=4273"
echo.
echo [OK] Naragate is running!
echo   Web app:  http://localhost:%FRONTEND_PORT%
echo   API docs: http://localhost:%BACKEND_PORT%/docs
echo.
echo Open http://localhost:%FRONTEND_PORT% in your browser.
echo On first run you'll be guided through the setup wizard.

start "" "http://localhost:%FRONTEND_PORT%"
pause