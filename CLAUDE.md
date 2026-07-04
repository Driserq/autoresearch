# CLAUDE.md

Auto-loaded every session. Toolkit-development rules live in **`AGENTS.md`** — read it
before changing the plugin. This file is the **routing layer**: pick the right tool for
a task without being told. Full rationale + the research infra live in
**`research/README.md`**; deep per-command docs in **`guide/`**.

## Route by task

**Autonomous work → an `/autoresearch` command:**
- Iterate on a metric until it stops improving → `/autoresearch` (`Metric:` / `Verify:`)
- Fuzzy goal → Scope/Metric/Verify → `/autoresearch:plan`
- Bug hunt → `:debug` · errors to zero (test/type/lint/build) → `:fix`
- Security audit → `:security` · release → `:ship`
- Requirements/edge cases → `:probe`, `:scenario` · debate first → `:predict`, `:reason`
- Docs/wiki → `:learn` · improvements→PRDs → `:improve`
- Analyze a results TSV → `:evals` · regression gate before push → `:regression`
- Chains: `guide/chains-and-combinations.md` · ready configs: `guide/examples-by-domain.md`

**Research infra (see `research/README.md`):**
- Loop against **another** repo → `add_repo` then `research/loop-on-repo.md`
- SQL over CSV/Parquet, dataframes, stats → `duckdb`/`pandas`/`polars`/`scipy` in `.venv`
- Capture loop iterations as data → `research/lib/runlog.py`; analyze/plot → `analyze.py`
- New experiment → copy `research/experiments/_template/`

**Environment tools:**
- Any chart/graph/dashboard → **`dataviz` skill** (read before writing chart code)
- Multi-source fact-checked report → **`deep-research` skill**
- Current library/framework docs → **Context7 MCP** · product analytics → **PostHog MCP**
- Quick web fact → `WebSearch` / `WebFetch`

## Guardrails
- The environment is ephemeral; `research/bootstrap.sh` re-provisions the `.venv` at
  session start. Don't hand-install the data stack — run/trust the hook.
- A metric is a **single scalar with a direction**, emitted as `SCORE: <n>` + exit code.
  If a request lacks one, reach for `:plan` before looping.
- Autoresearch safety hooks (scout-block, privacy-block, dangerous-cmd-block) are active
  and fail open — respect a block instead of working around it.
