# Running loops against another repository

The `/autoresearch` loop optimizes a **mechanical metric** on whatever code is in
scope. To point it at a *different* repo (not this toolkit), bring that repo into
the session and give the loop an isolated place to work so parallel candidates
don't collide.

## Flow

1. **Add the target repo to the session.**
   Ask Claude: *"add `owner/repo` to the session"* (it calls `add_repo`, which
   verifies access and clones into the workspace). The repo must be one your
   account can reach — check with `list_repos` if unsure.

2. **Isolate iterations.**
   Run candidates in a throwaway git worktree so a rejected change never dirties
   the base tree, and parallel candidates can't clobber each other:
   - one-off exploration → `EnterWorktree` / a manual `git worktree add`;
   - fan-out (several candidates at once) → spawn agents with `isolation: 'worktree'`.
   Worktrees are auto-cleaned if left unchanged.

3. **Define the metric + verify (a single scalar).**
   Copy `research/score-template.sh` (or `research/experiments/_template/run.py`)
   into the target and make it emit `SCORE: <n>` with a clean exit code. This is
   the keep/discard signal — vague "better" won't do.

4. **Run the loop.**
   ```
   /autoresearch Metric: <what SCORE means, + direction>
                 Verify: bash score.sh
   ```
   or hand it a plain-language goal and let the orchestrator derive the predicate.

5. **Capture each iteration as data** (so `evals`/`analyze.py` can reason about it):
   ```bash
   .venv/bin/python research/lib/runlog.py append \
     --experiment <target> --iteration <n> --score <s> --tokens <t> --kept <true|false>
   .venv/bin/python research/lib/analyze.py --experiment <target>
   ```

## Worked example — cut a target repo's p95 latency

```bash
# 1. bring it in
#    (ask Claude) add acme/api to the session
# 2. isolate
git -C acme-api worktree add ../acme-api-cand HEAD
# 3. metric: a script that benchmarks and prints SCORE (lower_is_better → negate)
#    ../acme-api-cand/score.sh  →  "SCORE: -142"   (142ms p95)
# 4. loop
#    /autoresearch Metric: p95 latency ms, lower is better  Verify: bash ../acme-api-cand/score.sh
# 5. log + analyze as it runs
```

See also: `guide/chains-and-combinations.md` (command pipelines) and
`guide/examples-by-domain.md` (ready-made Metric/Verify configs per language).
