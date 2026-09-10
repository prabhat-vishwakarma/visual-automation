#!/usr/bin/env bash
# Convenience wrapper: ensures Chromium's shared libraries are available
# (no-root fallback via tools/ensure_chromium_deps.py) then runs the app.
#
# Usage:
#   ./run.sh --config config/local-test.yaml
#   ./run.sh            # defaults to config/site.yaml
set -euo pipefail

cd "$(dirname "$0")"

PYTHON=".venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "No virtualenv found. Create one first:" >&2
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if [ "${SKIP_CHROMIUM_DEPS:-0}" = "1" ]; then
  exec "$PYTHON" -m app.main "$@"
fi

exec "$PYTHON" -m tools.ensure_chromium_deps --command ".venv/bin/python -m app.main $*"