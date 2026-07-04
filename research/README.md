# Research environment

Infrastructure for **conducting research in this repo** — running autoresearch
loops against real targets and doing data experiments — on top of the autoresearch
toolkit. Everything here is additive; it doesn't touch the published plugin.

> Web containers are **ephemeral** (rebuilt each session), so anything that must
> persist is committed here and re-provisioned automatically. See "How it's wired".

---

## Decision guide — what to use for which task

This is the router. It's also surfaced in the repo-root `CLAUDE.md` so Claude
consults it automatically; you shouldn't have to hand-direct tool choice.

### Autonomous loops & workflows (the 14 commands)

| You want to… | Use | Guide |
|---|---|---|
| Iterate on a metric until it stops improving | `/autoresearch` (or `Metric:`/`Verify:`) | `guide/autoresearch.md` |
| Turn a fuzzy goal into Scope/Metric/Verify first | `/autoresearch:plan` | `guide/autoresearch-plan.md` |
| Hunt a specific bug (hypothesize → falsify) | `/autoresearch:debug` | `guide/autoresearch-debug.md` |
| Drive tests/types/lint/build errors to zero | `/autoresearch:fix` | `guide/autoresearch-fix.md` |
| STRIDE/OWASP security audit | `/autoresearch:security` | `guide/autoresearch-security.md` |
| Stage → deploy → verify a release | `/autoresearch:ship` | `guide/autoresearch-ship.md` |
| Interrogate requirements / generate edge cases | `/autoresearch:probe`, `:scenario` | `guide/autoresearch-probe.md` |
| Debate a change before doing it | `/autoresearch:predict`, `:reason` | `guide/autoresearch-predict.md` |
| Generate docs / a wiki knowledge base | `/autoresearch:learn` | `guide/autoresearch-learn.md` |
| Research challenges → PRDs | `/autoresearch:improve` | `guide/autoresearch-improve.md` |
| Analyze an iteration results TSV | `/autoresearch:evals` | `guide/autoresearch-evals.md` |
| Gate against regressions before pushing | `/autoresearch:regression` | `guide/autoresearch-regression.md` |
| Chain several of the above | — | `guide/chains-and-combinations.md` |
| Find a ready Metric/Verify for your language | — | `guide/examples-by-domain.md` |

### Research infrastructure (added here)

| You want to… | Use |
|---|---|
| Run a loop against **another** repo | `add_repo` → `research/loop-on-repo.md` |
| SQL over a local CSV/Parquet/JSON with no server | `duckdb` (Python, in `.venv`) |
| SQL over a **remote** file / S3 URL | `duckdb` + `LOAD httpfs` (auto-staged; needs Full network) |
| Dataframes / stats / significance test | `pandas`, `polars`, `scipy` (in `.venv`) |
| Capture loop iterations as data | `research/lib/runlog.py` |
| Convergence / plateau / cost-per-token / plot | `research/lib/analyze.py` |
| Start a new experiment | copy `research/experiments/_template/` |
| A mechanical metric script (bash) | `research/score-template.sh` |

### Environment tools (skills & MCP)

| You want to… | Use |
|---|---|
| Any chart, graph, or dashboard | **`dataviz` skill** (read it *before* writing chart code) |
| Multi-source, fact-checked research report | **`deep-research` skill** |
| Current, version-correct library/framework docs | **Context7 MCP** (`.mcp.json`) |
| Product analytics on the Rouse Alarm project | **PostHog MCP** (already connected) |
| A quick fact off the web | `WebSearch` / `WebFetch` |

---

## Quick start

```bash
# provision (auto-runs at session start; safe to run by hand)
bash research/bootstrap.sh
source .venv/bin/activate            # or prefix commands with .venv/bin/

# log a couple of iterations, then analyze
python research/lib/runlog.py append --experiment demo --iteration 0 --score 0.40 --tokens 5000 --kept true
python research/lib/runlog.py append --experiment demo --iteration 1 --score 0.55 --tokens 4800 --kept true
python research/lib/analyze.py --experiment demo         # summary + research/runs/demo.png
```

## How it's wired

- **`bootstrap.sh`** + **`.claude/settings.json`** (`SessionStart` hook) reinstall the
  data stack (`requirements.txt`) into `./.venv` on every fresh container. Idempotent,
  fails open — it can never block startup. Heavier extras: `requirements-optional.txt`.
- **`.mcp.json`** wires the Context7 MCP server (keyless by default; add
  `CONTEXT7_API_KEY` for private libs / higher limits).
- **Remote DuckDB:** `bootstrap.sh` pre-stages the `httpfs` extension with `curl`
  (DuckDB's own downloader trips on the security proxy). After that,
  `LOAD httpfs` reads `https://…`/`s3://…` files directly. This needs **Full**
  network access (or a **Custom** allowlist including `extensions.duckdb.org` plus
  your data hosts); on **Trusted**/**None** it's skipped and local files still work.
- **`lib/`** is stdlib-only on the write path, so you can log runs before the stack
  is installed; analysis needs the `.venv`.
- `research/runs/` (raw logs + plots) and `.venv/` are git-ignored.

## Layout

```
research/
  README.md                     # this file — the decision guide
  bootstrap.sh                  # idempotent provisioner (SessionStart hook target)
  requirements.txt              # core data stack (auto-installed)
  requirements-optional.txt     # jupyter/seaborn/sklearn/statsmodels (on demand)
  loop-on-repo.md               # pointing loops at repos added via add_repo
  score-template.sh             # the SCORE:/exit-code metric contract, in bash
  lib/
    runlog.py                   # append/load iteration records (JSONL)
    analyze.py                  # convergence, plateau, cost-efficiency, plot
  experiments/
    _template/                  # copy this to start an experiment
      experiment.md             # hypothesis / metric / method / results
      run.py                    # skeleton that prints SCORE: <n>
  runs/                         # (git-ignored) per-experiment JSONL + PNGs
```
