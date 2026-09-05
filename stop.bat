@echo off
REM Stop Naragate (Windows)
cd /d "%~dp0"
docker compose down
echo Naragate stopped. Run start.bat to start it again.
pause