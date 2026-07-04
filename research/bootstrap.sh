#!/usr/bin/env bash
# research/bootstrap.sh — idempotent provisioner for the research environment.
#
# Runs on every fresh (ephemeral) web container via the SessionStart hook in
# .claude/settings.json, and is safe to run by hand any time.
#
# What it does:
#   1. creates a repo-local ./.venv and installs the Python data stack (uv);
#   2. best-effort pre-stages DuckDB's httpfs extension so remote reads
#      (http/https/S3) work — DuckDB's own downloader trips on the security
#      proxy, but curl + a local stage does not. Needs Full (or a Custom allowlist
#      that includes extensions.duckdb.org) network access; skipped otherwise.
#
# Design rules:
#   - Idempotent : fast no-op once provisioned; also self-heals the extension if
#                  network access was widened after the first run.
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

# Pre-stage an official DuckDB extension into the local extension dir so LOAD
# finds it without a network fetch. Idempotent; fail-open.
stage_duckdb_ext() {
  local ext="$1" ver plat dir dst
  have curl || return 0
  ver="$("$VENV/bin/python" -c 'import duckdb;print(duckdb.__version__)' 2>/dev/null)" || return 0
  [ -n "$ver" ] || return 0
  case "$(uname -m)" in
    x86_64|amd64)  plat="linux_amd64" ;;
    aarch64|arm64) plat="linux_arm64" ;;
    *) return 0 ;;
  esac
  dir="$HOME/.duckdb/extensions/v${ver}/${plat}"
  dst="$dir/${ext}.duckdb_extension"
  [ -f "$dst" ] && return 0
  mkdir -p "$dir"
  if curl -fsSL "https://extensions.duckdb.org/v${ver}/${plat}/${ext}.duckdb_extension.gz" \
        -o "/tmp/ddb-${ext}.gz" 2>>"$LOG" && gunzip -c "/tmp/ddb-${ext}.gz" > "$dst" 2>>"$LOG"; then
    log "staged duckdb extension: $ext (v$ver/$plat)"
  else
    rm -f "$dst"
    log "duckdb extension '$ext' not staged — needs Full network (extensions.duckdb.org). Local files still work."
  fi
}

# Fast path: this container is already provisioned.
if [ -f "$MARKER" ] && [ -x "$VENV/bin/python" ]; then
  stage_duckdb_ext httpfs   # cheap no-op if present; self-heals if network widened
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

stage_duckdb_ext httpfs

exit 0
