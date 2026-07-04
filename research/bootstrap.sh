#!/usr/bin/env bash
# research/bootstrap.sh — idempotent provisioner for the research environment.
#
# Runs on every fresh (ephemeral) web container via the SessionStart hook in
# .claude/settings.json, and is safe to run by hand any time.
#
# What it does: creates a repo-local ./.venv and installs the Python data stack
# (research/requirements.txt) with uv. That's it — deliberately minimal so it
# never turns session startup into a long wait.
#
# Design rules:
#   - Idempotent : fast no-op once provisioned (marker file), re-runnable.
#   - Fail open  : ALWAYS exits 0 so it can never block session startup.
#   - Quiet-ish  : one summary line to stdout; full detail in research/.bootstrap.log
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
REQ="$ROOT/research/requirements.txt"
MARKER="$VENV/.ar-research-provisioned"
LOG="$ROOT/research/.bootstrap.log"

: > "$LOG" 2>/dev/null || true
log()  { printf '%s\n' "$*" >>"$LOG" 2>/dev/null; }
have() { command -v "$1" >/dev/null 2>&1; }

# Fast path: this container is already provisioned.
if [ -f "$MARKER" ] && [ -x "$VENV/bin/python" ]; then
  echo "[research] env ready — source .venv/bin/activate"
  exit 0
fi

if ! have uv; then
  echo "[research] uv not found; skipping data-stack install (see $LOG)"
  log  "uv missing — install from https://astral.sh/uv, then re-run research/bootstrap.sh"
  exit 0
fi

echo "[research] provisioning data stack with uv (first run in a fresh container)…"
if uv venv "$VENV" >>"$LOG" 2>&1 \
   && uv pip install --python "$VENV/bin/python" -r "$REQ" >>"$LOG" 2>&1; then
  touch "$MARKER"
  echo "[research] data stack ready — source .venv/bin/activate  ($(wc -l <"$REQ") core packages)"
else
  echo "[research] data-stack install hit an error — see $LOG (session continues)"
fi

exit 0
