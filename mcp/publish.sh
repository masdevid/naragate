#!/usr/bin/env bash
# Build and upload naragate-mcp to PyPI.
#
# The API token is read from $PYPI_TOKEN, falling back to PYPI_TOKEN=... in the
# repo-root .env. It is never printed or passed on the command line.
#
# Usage:
#   mcp/publish.sh              # publish to PyPI
#   mcp/publish.sh testpypi     # publish to TestPyPI
#   mcp/publish.sh check        # dry run: build + twine check only (no token, no upload)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$HERE"

TARGET="${1:-pypi}"

if [[ "$TARGET" != "check" ]]; then
  if [[ -z "${PYPI_TOKEN:-}" && -f "$ROOT/.env" ]]; then
    PYPI_TOKEN="$(grep -E '^[[:space:]]*PYPI_TOKEN[[:space:]]*=' "$ROOT/.env" | tail -n1 | cut -d= -f2- \
      | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")"
  fi

  if [[ -z "${PYPI_TOKEN:-}" ]]; then
    echo "ERROR: PYPI_TOKEN is not set. Add PYPI_TOKEN=... to $ROOT/.env or export it." >&2
    exit 1
  fi
fi

echo "Building naragate-mcp (target: $TARGET)"
python -m pip install --upgrade --quiet build twine
rm -rf dist build
python -m build
python -m twine check dist/*

if [[ "$TARGET" == "check" ]]; then
  echo "Dry run OK: distributions built and validated; skipping upload."
  exit 0
fi

REPO_ARG=""
[[ "$TARGET" == "testpypi" ]] && REPO_ARG="--repository testpypi"

echo "Uploading to $TARGET (token hidden)"
# Username is the literal __token__; the password comes from the env var so it
# never appears in process arguments or logs.
TWINE_USERNAME="__token__" TWINE_PASSWORD="$PYPI_TOKEN" python -m twine upload $REPO_ARG dist/*
