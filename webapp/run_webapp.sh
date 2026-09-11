#!/usr/bin/env bash
# Owner-gated web demo: http://127.0.0.1:8710
# Never binds beyond 127.0.0.1.
set -euo pipefail
cd "$(dirname "$0")/.."

[ -x .venv/bin/python ] || { echo "No .venv found. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r webapp/requirements.txt"; exit 1; }

exec .venv/bin/python -m webapp.server