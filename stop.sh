#!/usr/bin/env bash
# Stop Naragate (macOS / Linux)
set -euo pipefail
cd "$(dirname "$0")"
docker compose down
echo "Naragate stopped. Run ./start.sh to start it again."