#!/usr/bin/env bash
# score-template.sh — the mechanical-metric contract for a loop, in bash.
#
# Mirrors this repo's scripts/score-*.sh convention: emit a single number and a
# clean exit code so /autoresearch (and CI) can key on it. Copy + adapt per target.
#
#   Usage:  research/score-template.sh [target-dir]
#   Output: a line "SCORE: <number>"   (higher_is_better here — flip as needed)
#   Exit:   0 = measured OK, non-zero = could not measure (loop treats as failure)
set -uo pipefail

TARGET="${1:-.}"

# --- replace with your real measurement ------------------------------------
# Example A — count passing tests (higher is better):
#   score=$(cd "$TARGET" && npm test --silent 2>/dev/null | grep -c 'passing')
#
# Example B — a scalar your Python experiment prints:
#   score=$(.venv/bin/python research/experiments/<name>/run.py | sed -n 's/^SCORE: //p')
#
# Example C — a lower-is-better metric (lint findings); negate so bigger = better:
#   findings=$(cd "$TARGET" && npx eslint . -f json 2>/dev/null | jq '[.[].messages[]] | length')
#   score=$(( -findings ))
#
# Demo stand-in so the template runs out of the box:
score=0
# ---------------------------------------------------------------------------

if [ -z "${score:-}" ]; then
  echo "score-template: no measurement produced" >&2
  exit 1
fi
echo "SCORE: ${score}"
