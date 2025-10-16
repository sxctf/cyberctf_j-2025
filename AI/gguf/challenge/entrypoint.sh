#!/usr/bin/env bash
set -euo pipefail

python -c "import sys; print('Python', sys.version)"

python - <<'PY'
try:
  from importlib.metadata import version
  print('llama-cpp-python:', version('llama-cpp-python'))
except Exception as e:
  print('llama-cpp-python: <unknown> (', type(e).__name__, e, ')')
PY

exec uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 10
