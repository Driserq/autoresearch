# Experiment: <short name>

> Copy this folder to `research/experiments/<your-name>/` and fill it in.
> The whole point: turn "it got better" into a single number a loop can chase.

## Hypothesis
<What do you believe, stated so it can be proven wrong? e.g. "Raising the
simplify-gate threshold cuts kept-but-noisy iterations without lowering final score.">

## Metric (mechanical, single scalar)
- **Definition:** <exact computation — what `run.py` prints after `SCORE:`>
- **Direction:** higher_is_better | lower_is_better
- **Source of truth:** <file / query / command that produces the raw data>

## Method
1. <baseline: what config/state is iteration 0?>
2. <what changes each iteration?>
3. <how many iterations / stop condition?>

## Verify
```bash
# Must print a line "SCORE: <number>" and exit 0 on success.
.venv/bin/python research/experiments/<your-name>/run.py
```

## Log each iteration
```bash
.venv/bin/python research/lib/runlog.py append \
  --experiment <your-name> --iteration <n> --score <s> \
  --direction higher_is_better --tokens <t> --kept <true|false>
```

## Analyze
```bash
.venv/bin/python research/lib/analyze.py --experiment <your-name>
```

## Results
<Paste the analyze.py summary + link the PNG. State whether the hypothesis held.>
