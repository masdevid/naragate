#!/usr/bin/env bash
# Naragate quick-start script (macOS / Linux)
set -euo pipefail

cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=============================================="
echo "  Naragate — quick start"
echo "=============================================="

# 1. Docker check
if ! command -v docker >/dev/null 2>&1; then
  echo -e "${RED}Docker is not installed.${NC}"
  echo "Install Docker Desktop first:"
  echo "  macOS: https://www.docker.com/products/docker-desktop/"
  echo "  Windows: https://www.docker.com/products/docker-desktop/"
  echo "Then open Docker Desktop and re-run this script."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo -e "${RED}Docker is installed but not running.${NC}"
  echo "Open the Docker Desktop app and wait until it shows \"Engine running\","
  echo "then re-run this script."
  exit 1
fi

# 2. Ollama check (optional, only a warning)
if command -v ollama >/dev/null 2>&1; then
  if ! curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${YELLOW}Ollama is installed but not running.${NC}"
    echo "Start it (e.g. open the Ollama app), then pull a model:"
    echo "  ollama pull gemma3:12b"
  fi
else
  echo -e "${YELLOW}Ollama not detected.${NC}"
  echo "Naragate needs a local LLM. Install Ollama from https://ollama.com"
  echo "then pull a model, e.g.:  ollama pull gemma3:12b"
fi

# 3. .env bootstrap
if [ ! -f .env ]; then
  echo "Creating .env from .env.example ..."
  cp .env.example .env
  echo -e "${YELLOW}Created .env — you can leave it empty and set keys later in the web UI.${NC}"
fi

# 4. Start
echo "Starting Naragate (first run builds images, this can take a few minutes) ..."
docker compose up -d --build

# 5. Wait for backend health
BACKEND_PORT="${BACKEND_PORT:-5678}"
echo "Waiting for the backend on port ${BACKEND_PORT} ..."
for i in $(seq 1 60); do
  if curl -s -m 2 "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo -e "${RED}Backend did not become ready in time.${NC}"
    echo "Run:  docker compose logs backend"
    exit 1
  fi
done

FRONTEND_PORT="${FRONTEND_PORT:-4273}"
echo -e "${GREEN}Naragate is running!${NC}"
echo "  Web app:  http://localhost:${FRONTEND_PORT}"
echo "  API docs: http://localhost:${BACKEND_PORT}/docs"
echo
echo "Open http://localhost:${FRONTEND_PORT} in your browser."
echo "On first run you'll be guided through the setup wizard."

# Open the browser (best effort)
if command -v open >/dev/null 2>&1; then
  open "http://localhost:${FRONTEND_PORT}"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://localhost:${FRONTEND_PORT}" >/dev/null 2>&1 || true
fi