# Experiment: optimizer-bot — differentiation vs free tools

## Hypothesis
A research-backed cost-comparison workflow (live prices + explicit unit-economics
math + citations) produces answers a blind judge prefers over a single-shot,
no-web answer (the free-ChatGPT/Perplexity proxy) — and the edge **grows with the
stakes** of the question. If true, "free tools already do this" is defeated.

## Metric (mechanical, single scalar)
- **Definition:** treatment (research workflow) win-rate over baseline across the
  question set, blind-judged. Secondary: mean rubric-total delta (treatment − baseline).
- **Direction:** higher_is_better
- **Break out by stakes tier** (trivial / mid / high) to locate where the edge is real.

## Method
1. Question set: 9 real comparison questions, 3 per stakes tier (below).
2. Treatment arm: an agent per question with live web research; returns the
   user-facing answer (verdict, $ and % magnitude, break-even, assumptions, sources).
3. Baseline arm: an agent per question, NO tools, single-shot from memory.
4. Blind judge: one independent agent scores both answers per question on 5 dims
   (correctness, specificity, actionability, sourcing, honesty; 0–5 each) and picks
   a winner, blind to arm identity.
5. Tabulate win-rate + rubric delta by tier (pandas/duckdb); chart it.

## Question set
- Trivial: (T1) toilet paper vs paper towel to blow your nose; (T2) boil 500ml water
  kettle vs microwave; (T3) dry hands at home paper towel vs small electric dryer.
- Mid: (M1) home-brew vs $5/day café coffee over a year; (M2) bottled water vs Brita
  pitcher per year (2-person); (M3) paper towels vs reusable Swedish dishcloths per year.
- High: (H1) lease vs buy a $30k car over 5 years; (H2) repair vs replace a 7-yr-old
  fridge (compressor); (H3) electric vs natural-gas clothes dryer over its lifetime.

## Verify / read
Judge JSON → win-rate + deltas by tier. Keep-signal: treatment win-rate ≥ ~70% overall
and clearly higher on mid/high tiers. Kill-signal for *this framing*: edge concentrated
only on trivial questions, or win-rate < 60%.

## Results
(filled after the run)
